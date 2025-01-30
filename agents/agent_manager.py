import json
from pathlib import Path
from typing import Dict, Any, List, Optional

class Agent:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.id = config.get("id")
        self.name = config.get("name")
        
    def process(self, input_text: str) -> str:
        """Process the input text according to agent configuration"""
        # 这里实现具体的处理逻辑
        return input_text  # 临时返回原文本，实际应该根据agent配置处理

class AgentManager:
    def __init__(self):
        self.agents: Dict[str, Agent] = {}
        self._load_agents()
    
    def _load_agents(self):
        """Load all agent configurations from the agents directory"""
        agents_dir = Path(__file__).parent.parent.parent / "agents"
        
        for agent_file in agents_dir.rglob("*.json"):
            try:
                with open(agent_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    agent = Agent(config)
                    self.agents[agent.id] = agent
            except Exception as e:
                print(f"Failed to load agent from {agent_file}: {str(e)}")
    
    def get_agent_list(self) -> List[str]:
        """Get list of available agent IDs"""
        return list(self.agents.keys())
    
    def get_agent(self, agent_id: str) -> Optional[Agent]:
        """Get agent by ID"""
        return self.agents.get(agent_id) 