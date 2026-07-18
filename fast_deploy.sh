#!/bin/bash

# Fast Gateway Automated Termux Deployer
# Language: English

# Colors for terminal
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
YELLOW='\033[1;33m'
NC_PLAIN='\033[0m'

clear
echo -e "${BLUE}==================================================${NC_PLAIN}"
echo -e "${CYAN}          Fast Gateway Automated Deployer         ${NC_PLAIN}"
echo -e "${BLUE}==================================================${NC_PLAIN}"
echo ""

# Check dependencies
echo -e "${YELLOW}[*] Checking required dependencies...${NC_PLAIN}"
for cmd in curl git jq; do
    if ! command -v $cmd &> /dev/null; then
        echo -e "${YELLOW}[!] $cmd is missing. Installing...${NC_PLAIN}"
        pkg install $cmd -y || apt install $cmd -y
    fi
done
echo -e "${GREEN}[+] Dependencies are ready!${NC_PLAIN}"
echo ""

# Choose Platform
echo -e "${CYAN}Select Cloud Platform to Deploy:${NC_PLAIN}"
echo -e "1) Render.com (Recommended for Cloudflare Clean IPs)"
echo -e "2) Railway.app"
read -p "Enter choice (1 or 2): " platform_choice

if [ "$platform_choice" = "1" ]; then
    echo ""
    echo -e "${CYAN}--- Render.com Deployment ---${NC_PLAIN}"
    echo -e "Please get your API Key from Render Dashboard -> Account Settings -> API Keys"
    read -p "Enter your Render API Key: " RENDER_TOKEN

    if [ -z "$RENDER_TOKEN" ]; then
        echo -e "${RED}[-][Error] API Key cannot be empty!${NC_PLAIN}"
        exit 1
    fi

    # Validate Token
    echo -e "${YELLOW}[*] Validating API Key...${NC_PLAIN}"
    VALIDATION=$(curl -s -H "Authorization: Bearer $RENDER_TOKEN" https://api.render.com/v1/owners?limit=1)
    
    if echo "$VALIDATION" | grep -q "id"; then
        OWNER_ID=$(echo "$VALIDATION" | jq -r '.[0].owner.id')
        echo -e "${GREEN}[+] Token is valid! Owner ID verified.${NC_PLAIN}"
    else
        echo -e "${RED}[-][Error] Invalid API Key or network issue. Please check your token.${NC_PLAIN}"
        exit 1
    fi

    # App Details
    echo ""
    read -p "Enter unique Application Name (e.g., fastpanel123): " APP_NAME
    APP_NAME=$(echo "$APP_NAME" | tr '[:upper:]' '[:lower:]' | tr -cd 'a-z0-9-')
    
    if [ -z "$APP_NAME" ]; then
        APP_NAME="fast-panel-$RANDOM"
        echo -e "${YELLOW}[!] Empty name. Using auto-generated: $APP_NAME${NC_PLAIN}"
    fi

    echo ""
    echo -e "${CYAN}Select Deployment Region:${NC_PLAIN}"
    echo -e "1) Frankfurt (Germany) - Recommended"
    echo -e "2) Oregon (USA)"
    echo -e "3) Ohio (USA)"
    echo -e "4) Singapore"
    read -p "Enter region choice (1-4) [Default: 1]: " reg_choice
    case $reg_choice in
        2) REGION="oregon" ;;
        3) REGION="ohio" ;;
        4) REGION="singapore" ;;
        *) REGION="frankfurt" ;;
    esac

    # Create Service JSON (Connected to your Lvateam-IR/fast-panel repository)
    JSON_DATA=$(cat <<EOF
{
  "type": "web_service",
  "name": "$APP_NAME",
  "ownerId": "$OWNER_ID",
  "repo": "https://github.com/Lvateam-IR/fast-panel",
  "branch": "main",
  "env": "python",
  "autoDeploy": "yes",
  "serviceDetails": {
    "envSpecificDetails": {
      "buildCommand": "pip install -r requirements.txt",
      "startCommand": "gunicorn main:app"
    },
    "plan": "free",
    "region": "$REGION"
  },
  "envVars": [
    {
      "key": "SECRET_KEY",
      "value": "fast-gateway-secret-$(date +%s)"
    }
  ]
}
EOF
)

    echo -e "${YELLOW}[*] Initiating deployment on Render...${NC_PLAIN}"
    DEPLOY_REQ=$(curl -s -X POST https://api.render.com/v1/services \
      -H "Authorization: Bearer $RENDER_TOKEN" \
      -H "Content-Type: application/json" \
      -d "$JSON_DATA")

    SERVICE_URL=$(echo "$DEPLOY_REQ" | jq -r '.service.url')

    if [ "$SERVICE_URL" != "null" ] && [ ! -z "$SERVICE_URL" ]; then
        echo ""
        echo -e "${GREEN}==================================================${NC_PLAIN}"
        echo -e "${GREEN}🎉 DEPLOYMENT REQUEST SUBMITTED SUCCESSFUL!       ${NC_PLAIN}"
        echo -e "${GREEN}==================================================${NC_PLAIN}"
        echo -e "${CYAN}Application Name:${NC_PLAIN} $APP_NAME"
        echo -e "${CYAN}Region:${NC_PLAIN} $REGION"
        echo -e "${CYAN}Panel URL:${NC_PLAIN} ${SERVICE_URL}/login"
        echo -e "${CYAN}Default Password:${NC_PLAIN} admin"
        echo ""
        echo -e "${YELLOW}[Note] Please wait 2-3 minutes for Render to completely build and launch the server.${NC_PLAIN}"
    else
        echo -e "${RED}[-][Error] Failed to deploy. Server Response:${NC_PLAIN}"
        echo "$DEPLOY_REQ" | jq .
    fi

elif [ "$platform_choice" = "2" ]; then
    echo ""
    echo -e "${CYAN}--- Railway.app Deployment ---${NC_PLAIN}"
    echo -e "Please get your API Token from Railway -> Account Settings -> Tokens"
    read -p "Enter your Railway API Token: " RAILWAY_TOKEN

    if [ -z "$RAILWAY_TOKEN" ]; then
        echo -e "${RED}[-][Error] API Token cannot be empty!${NC_PLAIN}"
        exit 1
    fi

    echo ""
    read -p "Enter unique Project Name (e.g., fastpanel123): " PROJECT_NAME
    if [ -z "$PROJECT_NAME" ]; then
        PROJECT_NAME="fast-project-$RANDOM"
    fi

    # Create Project via GQL directly (This automatically validates the token)
    echo -e "${YELLOW}[*] Validating Token & Creating Project on Railway...${NC_PLAIN}"
    CREATE_PROJ_GQL="{\"query\": \"mutation { projectCreate(input: { name: \\\"$PROJECT_NAME\\\" }) { id } }\"}"
    PROJECT_REQ=$(curl -s -X POST https://backboard.railway.app/graphql \
      -H "Authorization: Bearer $RAILWAY_TOKEN" \
      -H "Content-Type: application/json" \
      -d "$CREATE_PROJ_GQL")

    PROJECT_ID=$(echo "$PROJECT_REQ" | jq -r '.data.projectCreate.id')

    if [ "$PROJECT_ID" = "null" ] || [ -z "$PROJECT_ID" ]; then
        echo -e "${RED}[-][Error] Invalid Railway Token or failed to create project.${NC_PLAIN}"
        echo "$PROJECT_REQ" | jq .
        exit 1
    fi
    
    echo -e "${GREEN}[+] Token Verified & Project Created! ID: $PROJECT_ID${NC_PLAIN}"
    echo -e "${YELLOW}[*] Attaching fast-panel repository pipeline...${NC_PLAIN}"
    
    # Template deployment mutation using your repository path
    DEPLOY_GQL="{\"query\": \"mutation { serviceCreate(input: { projectId: \\\"$PROJECT_ID\\\", source: { repo: \\\"Lvateam-IR/fast-panel\\\" } }) { id } }\"}"
    SERVICE_REQ=$(curl -s -X POST https://backboard.railway.app/graphql \
      -H "Authorization: Bearer $RAILWAY_TOKEN" \
      -H "Content-Type: application/json" \
      -d "$DEPLOY_GQL")
      
    echo ""
    echo -e "${GREEN}==================================================${NC_PLAIN}"
    echo -e "${GREEN}🎉 DEPLOYMENT REQUEST INITIALIZED SUCCESSFUL!     ${NC_PLAIN}"
    echo -e "${GREEN}==================================================${NC_PLAIN}"
    echo -e "${CYAN}Project Name:${NC_PLAIN} $PROJECT_NAME"
    echo -e "${CYAN}Project Dashboard:${NC_PLAIN} https://railway.app/project/$PROJECT_ID"
    echo -e "${CYAN}Default Password:${NC_PLAIN} admin"
    echo ""
    echo -e "${YELLOW}[Note] Go to the dashboard link above to view your generated public URL under service settings once build completes.${NC_PLAIN}"

else
    echo -e "${RED}Invalid Selection! Exiting...${NC_PLAIN}"
    exit 1
fi
