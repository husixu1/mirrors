#!/bin/sh

read -p "Sync Tool: " tool
cp -i _basicTemplate $tool"Template"
cp -i _basicInitTemplate $tool"InitTemplate"
read -p "Edit tool(default vim): " editTool
${editTool:-vim} $tool"Template"
${editTool:-vim} $tool"InitTemplate"

