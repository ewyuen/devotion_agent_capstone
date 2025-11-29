# Devotion Agent Capstone

A Python-based agent system for processing and analyzing devotion-related data.

## Project Structure

```
devotion_agent_capstone/
├── devotion_agents.py      # Core agent implementation
├── devotion_tools.py       # Tool definitions for agents
├── DevotionAgent.ipynb     # Jupyter notebook for interactive exploration
├── data/
│   └── devotion.xml        # XML data source
└── README.md               # This file
```

## Files

- **devotion_agents.py** - Contains the main agent logic and orchestration
- **devotion_tools.py** - Defines tools and utilities used by the agents
- **DevotionAgent.ipynb** - Interactive Jupyter notebook for experimentation and analysis
- **data/devotion.xml** - XML dataset with devotion-related information

## Getting Started

1. Create a `.env` file in the project root directory with your Gemini API key:
   ```
   GEMINI_API_KEY=your_actual_api_key_here
   ```
   You can get your API key from [Google AI Studio](https://ai.google.dev)

2. Install required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Run the agent:
   ```bash
   python DevotionAgent.py
   ```

4. Or explore interactively:
   ```bash
   jupyter notebook DevotionAgent.ipynb
   ```

## Requirements

- Python 3.7+
- Dependencies listed in requirements.txt

## License

[Add your license information here]
