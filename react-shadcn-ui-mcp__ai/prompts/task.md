# ShadCN UI Implementation Outline

## Login Page
- Card: Container for the login form
- Input: For email and password fields
- Label: For form field labels
- Button: For the login action
- Form: To structure the login form
- Alert or Toast: For error/success messages

## Dashboard Page
- Grid or SimpleGrid: To layout the MCP server cards
- Card: Each MCP server is represented as a card
- Avatar or Image: For server icons or images on cards
- Badge: To show server status (e.g., online/offline)
- Typography (Heading, Text): For server name and metadata

## Server Detail View (after clicking a card)
- Card or Sheet/Drawer: For the detailed view container
- Image: Header image for the server
- Badge: Server status
- List or DescriptionList: For metadata (name, region, version, etc.)
- Collapsible or Accordion: For installation steps (bubble cards or collapsible UI)
- Stepper or Progress: If showing step-by-step installation visually
- Button: For actions (e.g., copy install command)

## Layout & Navigation
- AppShell or Layout: For consistent page structure
- Navbar or Sidebar: For navigation (if needed)
- Header: For page titles or user info
