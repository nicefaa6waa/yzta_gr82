#!/bin/bash
# filepath: /home/churchy/website/render-build.sh

echo "🚀 Starting Render build process..."

# Create persistent data directory
mkdir -p /opt/render/project/src/data
echo "📁 Created persistent data directory"

# Install Python dependencies
pip install -r requirements.txt
echo "📦 Dependencies installed"

# Initialize databases
python -c "
from database.database import db
from database.chat_db import ChatDB
print('✅ Databases initialized')
chat_db = ChatDB()
print('✅ Chat database initialized')
"

echo "🎉 Build completed successfully"