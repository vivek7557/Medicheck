from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
import asyncio
import logging
from pydantic import BaseModel, Field

from memory.session_service import SessionService
from memory.memory_bank import MemoryBank
from observability.logger import Logger
from protocols.a2a_protocol import A2AMessage

class BaseAgent(ABC):
    """
    Abstract base class for all medical agents.
    Provides common functionality for LLM interaction, memory management, and communication.
    """
    
    def __init__(self, agent_id: str, name: str, description: str):
        self.agent_id = agent_id
        self.name = name
        self.description = description
        self.session_service = SessionService()
        self.memory_bank = MemoryBank()
        self.logger = Logger(self.name)
        self._running = False
        
    @abstractmethod
    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the agent's primary function with the given input.
        """
        pass
    
    async def process_with_memory(self, input_data: Dict[str, Any], session_id: str) -> Dict[str, Any]:
        """
        Process input with access to memory and session context.
        """
        # Retrieve session context
        session_context = await self.session_service.get_session(session_id)
        
        # Retrieve relevant memories
        relevant_memories = await self.memory_bank.search_similar(
            query=str(input_data),
            session_id=session_id,
            limit=5
        )
        
        # Add context to input
        enhanced_input = {
            **input_data,
            "context": session_context,
            "memories": relevant_memories
        }
        
        # Execute the agent's logic
        result = await self.execute(enhanced_input)
        
        # Store the interaction in memory
        await self.memory_bank.store_interaction(
            session_id=session_id,
            agent_id=self.agent_id,
            input_data=input_data,
            output_data=result
        )
        
        return result
    
    async def communicate_with_agent(self, target_agent_id: str, message: A2AMessage) -> Optional[A2AMessage]:
        """
        Send a message to another agent using the A2A protocol.
        """
        from protocols.message_bus import MessageBus
        message_bus = MessageBus()
        
        try:
            response = await message_bus.send_message(target_agent_id, message)
            return response
        except Exception as e:
            self.logger.error(f"Failed to communicate with agent {target_agent_id}: {str(e)}")
            return None
    
    async def run_loop(self, input_queue: asyncio.Queue, output_queue: asyncio.Queue):
        """
        Run the agent in a continuous loop, processing inputs from the queue.
        """
        self._running = True
        while self._running:
            try:
                # Get input from queue (with timeout to allow checking _running flag)
                input_data = await asyncio.wait_for(input_queue.get(), timeout=1.0)
                
                # Process the input
                result = await self.execute(input_data)
                
                # Put result in output queue
                await output_queue.put(result)
                
                # Mark task as done
                input_queue.task_done()
                
            except asyncio.TimeoutError:
                # Check if we should continue running
                continue
            except Exception as e:
                self.logger.error(f"Error in agent loop: {str(e)}")
                continue
    
    def stop(self):
        """
        Stop the agent's loop.
        """
        self._running = False
    
    async def pause_operation(self, pause_duration: float = 0.0):
        """
        Pause the agent's operation for a specified duration or indefinitely.
        """
        if pause_duration > 0:
            await asyncio.sleep(pause_duration)
        else:
            # For indefinite pause, we would need a more sophisticated mechanism
            # This is a simplified implementation
            pass
    
    async def resume_operation(self):
        """
        Resume the agent's operation after a pause.
        """
        pass  # Resume logic would go here if needed