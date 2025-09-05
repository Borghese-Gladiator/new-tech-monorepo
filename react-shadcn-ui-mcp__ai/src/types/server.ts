export type Server = {
  id: string;
  name: string;
  status: 'online' | 'offline' | 'unknown';
  region: string;
  version: string;
  image: string;
  installSteps: string[];
};
