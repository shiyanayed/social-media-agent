# LangChain Agent Skill

## Role
You are a LangChain expert building an AI agent that 
coordinates research, writing, video creation, 
and social media posting.

## When To Use
Use this skill when building agent.py and 
connecting all tools together.

## Step-by-Step Workflow
1. Define each tool as a LangChain Tool object
2. Use Gemini 2.5 Flash as the primary LLM
3. If Gemini fails, automatically fall back to Groq
4. Use AgentType.STRUCTURED_CHAT_ZERO_SHOT_REACT 
5. Give the agent a clear system prompt per niche
6. Chain tools in this order:
   research → write → create_video → upload

## Niche System Prompts
Football: "You are a passionate football analyst..."
Movies: "You are a witty movie critic..."
Anime: "You are an expressive anime fan..."
Crypto: "You are an analytical crypto commentator..."

## Constraints
- Always handle LLM timeout errors
- Log every agent step for debugging
- Never let one tool failure crash the whole agent
- Return structured JSON from every tool