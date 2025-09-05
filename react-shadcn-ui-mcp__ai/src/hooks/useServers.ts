import { useState } from 'react';
import { Server } from "@/types/server";

const MOCK_SERVERS: Server[] = [
  {
    id: '1',
    name: 'MCP Alpha',
    status: 'online',
    region: 'us-east',
    version: '1.0.0',
    image: 'https://placehold.co/600x200/EEE/31343C?text=MCP+Alpha',
    installSteps: [
      'Download the installer from the official site.',
      'Run the installer and follow the prompts.',
      'Verify installation with the CLI tool.'
    ]
  },
  {
    id: '2',
    name: 'MCP Beta',
    status: 'offline',
    region: 'eu-west',
    version: '1.2.3',
    image: 'https://placehold.co/600x200/EEE/31343C?text=MCP+Beta',
    installSteps: [
      'Clone the repository.',
      'Install dependencies.',
      'Start the server.'
    ]
  }
];

export function useServers() {
  const [servers] = useState<Server[]>(MOCK_SERVERS);
  return { servers };
}
