#!/bin/sh

read -p "Sync Tool: " tool
cp -i _basicTemplate $tool"Template"
read -p "Edit tool(default vim): " editTool
${editTool:-vim} $tool"Template"

