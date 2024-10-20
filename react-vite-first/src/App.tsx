import { useState } from 'react'
import reactLogo from './assets/react.svg'
import viteLogo from '/vite.svg'
import './App.css'

import {
  HoverCard,
  HoverCardContent,
  HoverCardTrigger,
} from "@/components/ui/hover-card";

function App() {
  return (
    <div className="flex justify-center  items-center h-screen">
      <HoverCard>
        <HoverCardTrigger className="rounded-xl text-white py-2 px-4 bg-slate-500">First Shadcn Component</HoverCardTrigger>
        <HoverCardContent className=" font-bold text-slate-500 w-max">My first of many components</HoverCardContent>
      </HoverCard>
    </div>
  )
}

export default App
