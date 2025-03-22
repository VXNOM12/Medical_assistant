# app/tkinter_gui.py
import sys
from pathlib import Path

# Add project root to Python path - MUST BE BEFORE OTHER IMPORTS
project_root = str(Path(__file__).parent.parent)
sys.path.append(project_root)

# Import the fix and integration modules first
from src.fix_templates import MedicalResponseTemplates
from src.fix_imports import ensure_imports
from src.inference_adapter import apply_process_input_mixin  # Import our adapter
from src.safety_adapter import ensure_safety_compatibility  # Import safety adapter
from src.medical_term_adapter import ensure_medical_term_compatibility  # Import medical term adapter
from src.integration import ensure_component_compatibility  # Import integration module


# Now import remaining modules
import tkinter as tk
from tkinter import scrolledtext, font, ttk
import re
import os
import threading
import time
import json
from src.response_templates import ResponseEnhancer
from src.inference import EnhancedMedicalChatbot as MedicalChatBot
from src.model.medical_model import MedicalModel

# Redundant try/except block can be simplified since we're using the alias above
try:
    # This is already handled by the import above, but keeping for robustness
    from src.inference import EnhancedMedicalChatbot as MedicalChatBot
except ImportError as e:
    print(f"Error importing MedicalChatBot: {e}")
    sys.exit(1)

class MedicalChatApp:
    def __init__(self, root):
        self.root = root
        try:
            self.bot = MedicalChatBot()
            print("Successfully initialized MedicalChatBot")
        except Exception as e:
            print(f"Error initializing MedicalChatBot: {e}")
            sys.exit(1)
            
        # Initialize conversation tracking
        self.current_conversation_id = None
        self.awaiting_follow_up = False
        self.conversation_active = False
        
        # Setup UI components
        self.setup_ui()
        
        # Configure typing animation
        self.typing_speed = 15  # characters per frame
        self.typing_animation = None
        self.typing_text = ""
        self.typing_position = 0
        
    def setup_ui(self):
        # Configure window
        self.root.title("Medical AI Assistant")
        self.root.geometry("900x700")
        self.root.configure(bg="#f0f0f0")
        
        # Create main frame with padding
        main_frame = tk.Frame(self.root, bg="#f0f0f0")
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Header
        header_frame = tk.Frame(main_frame, bg="#f0f0f0")
        header_frame.pack(fill=tk.X, pady=(0, 10))
        
        title_label = tk.Label(
            header_frame,
            text="Medical AI Assistant",
            font=("Helvetica", 24, "bold"),
            bg="#f0f0f0",
            fg="#2C3E50"
        )
        title_label.pack()
        
        subtitle_label = tk.Label(
            header_frame,
            text="Ask general health questions (Not for emergencies or diagnoses)",
            font=("Helvetica", 12, "italic"),
            bg="#f0f0f0",
            fg="#7F8C8D"
        )
        subtitle_label.pack()
        
        # Chat Area with conversation styling
        self.chat_frame = tk.Frame(main_frame, bg="#f0f0f0")
        self.chat_frame.pack(fill=tk.BOTH, expand=True)
        
        # Create a frame for the chat display with a border
        chat_display_frame = tk.Frame(
            self.chat_frame,
            bg="#FFFFFF",
            highlightbackground="#CCCCCC",
            highlightthickness=1,
            bd=0
        )
        chat_display_frame.pack(fill=tk.BOTH, expand=True)
        
        # Create the chat display with improved styling
        self.chat_display = scrolledtext.ScrolledText(
            chat_display_frame,
            font=("Arial", 12),
            wrap=tk.WORD,
            bg="#FFFFFF",
            fg="#2C3E50",
            padx=10,
            pady=10,
            bd=0,
            relief=tk.FLAT
        )
        self.chat_display.pack(fill=tk.BOTH, expand=True)
        self.chat_display.config(state=tk.DISABLED)
        
        # Configure text tags for different message types
        self.chat_display.tag_configure("user", foreground="#2C3E50", font=("Arial", 12, "bold"))
        self.chat_display.tag_configure("assistant", foreground="#27AE60", font=("Arial", 12, "bold"))
        self.chat_display.tag_configure("follow_up", foreground="#3498DB", font=("Arial", 12, "bold"))
        self.chat_display.tag_configure("error", foreground="#E74C3C", font=("Arial", 12))
        self.chat_display.tag_configure("system", foreground="#7F8C8D", font=("Arial", 10, "italic"))
        self.chat_display.tag_configure("disclaimer", foreground="#7F8C8D", font=("Arial", 10, "italic"))
        
        # Input Area with status indicator
        input_container = tk.Frame(main_frame, bg="#f0f0f0")
        input_container.pack(fill=tk.X, pady=(10, 0))
        
        # Status indicator frame
        status_frame = tk.Frame(input_container, bg="#f0f0f0")
        status_frame.pack(fill=tk.X, pady=(0, 5))
        
        # Status indicator (conversation state)
        self.status_var = tk.StringVar()
        self.status_var.set("")
        self.status_label = tk.Label(
            status_frame,
            textvariable=self.status_var,
            fg="#3498DB",
            bg="#f0f0f0",
            font=("Arial", 10, "italic"),
            anchor="w"
        )
        self.status_label.pack(side=tk.LEFT)
        
        # Conversation ID display
        self.conversation_id_var = tk.StringVar()
        self.conversation_id_label = tk.Label(
            status_frame,
            textvariable=self.conversation_id_var,
            fg="#7F8C8D",
            bg="#f0f0f0",
            font=("Arial", 8),
            anchor="e"
        )
        self.conversation_id_label.pack(side=tk.RIGHT)
        
        # Input frame
        input_frame = tk.Frame(input_container, bg="#f0f0f0")
        input_frame.pack(fill=tk.X)
        
        # Message entry with placeholder text
        self.entry_var = tk.StringVar()
        self.message_entry = tk.Entry(
            input_frame,
            textvariable=self.entry_var,
            font=("Arial", 12),
            bg="#FFFFFF",
            fg="#2C3E50",
            relief=tk.SOLID,
            bd=1
        )
        self.message_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))
        self.message_entry.bind("<Return>", lambda e: self.send_message())
        
        # Add placeholder text
        self.entry_var.set("Type your health question here...")
        self.message_entry.bind("<FocusIn>", self._on_entry_focus_in)
        self.message_entry.bind("<FocusOut>", self._on_entry_focus_out)
        
        # Button styles using ttk
        style = ttk.Style()
        style.configure("Send.TButton", foreground="#FFFFFF", background="#3498DB", font=("Arial", 12, "bold"))
        style.configure("Clear.TButton", foreground="#FFFFFF", background="#E74C3C", font=("Arial", 12, "bold"))
        style.configure("New.TButton", foreground="#FFFFFF", background="#27AE60", font=("Arial", 12, "bold"))
        
        # Send button
        send_button = ttk.Button(
            input_frame,
            text="Send",
            command=self.send_message,
            style="Send.TButton",
            width=10
        )
        send_button.pack(side=tk.LEFT)
        
        # New Conversation button
        new_conv_button = ttk.Button(
            input_frame,
            text="New Conversation",
            command=self.start_new_conversation,
            style="New.TButton",
            width=18
        )
        new_conv_button.pack(side=tk.LEFT, padx=(10, 0))
        
        # Clear button
        clear_button = ttk.Button(
            input_frame,
            text="Clear",
            command=self.clear_chat,
            style="Clear.TButton",
            width=10
        )
        clear_button.pack(side=tk.LEFT, padx=(10, 0))
        
        # Example Questions section with improved styling
        examples_frame = tk.LabelFrame(
            main_frame,
            text="Example Questions",
            font=("Arial", 11, "bold"),
            bg="#f0f0f0",
            fg="#7F8C8D",
            padx=10,
            pady=10
        )
        examples_frame.pack(fill=tk.X, pady=(15, 0))
        
        # Grid for example buttons
        examples_grid = tk.Frame(examples_frame, bg="#f0f0f0")
        examples_grid.pack(fill=tk.X)
        
        examples = [
            "What are common symptoms of seasonal allergies?",
            "How can I reduce cholesterol naturally?",
            "What's the recommended daily water intake?",
            "What causes frequent headaches?",
            "How do I manage lower back pain?",
            "What are normal blood pressure ranges?"
        ]
        
        # Create grid of example buttons
        row, col = 0, 0
        for example in examples:
            example_btn = tk.Button(
                examples_grid,
                text=example,
                command=lambda x=example: self.use_example(x),
                bg="#ECF0F1",
                fg="#2C3E50",
                relief=tk.FLAT,
                padx=5,
                pady=3,
                bd=0,
                font=("Arial", 10),
                anchor="w",
                cursor="hand2"
            )
            example_btn.grid(row=row, column=col, sticky="w", padx=5, pady=3)
            
            # Move to next column or row
            col += 1
            if col > 1:  # 2 columns
                col = 0
                row += 1
                
        # Status bar at the bottom
        status_bar = tk.Frame(main_frame, bg="#f0f0f0", height=20)
        status_bar.pack(fill=tk.X, pady=(10, 0))
        
        self.connection_status = tk.Label(
            status_bar,
            text="AI Assistant Ready",
            fg="#27AE60",
            bg="#f0f0f0",
            font=("Arial", 9),
            anchor="w"
        )
        self.connection_status.pack(side=tk.LEFT)
        
        # Current time on the right
        self.time_display = tk.Label(
            status_bar,
            text="",
            fg="#7F8C8D",
            bg="#f0f0f0",
            font=("Arial", 9),
            anchor="e"
        )
        self.time_display.pack(side=tk.RIGHT)
        
        # Update time
        self._update_time()
        
    def _on_entry_focus_in(self, event):
        """Handle focus in event for entry placeholder"""
        if self.entry_var.get() == "Type your health question here...":
            self.entry_var.set("")
            self.message_entry.config(fg="#2C3E50")
            
    def _on_entry_focus_out(self, event):
        """Handle focus out event for entry placeholder"""
        if not self.entry_var.get():
            self.entry_var.set("Type your health question here...")
            self.message_entry.config(fg="#95A5A6")
            
    def _update_time(self):
        """Update the time display in the status bar"""
        current_time = time.strftime("%H:%M:%S")
        self.time_display.config(text=current_time)
        self.root.after(1000, self._update_time)
            
    def send_message(self):
        """Send a message and process the response"""
        # Get message from entry
        message = self.entry_var.get().strip()
        if message == "Type your health question here...":
            message = ""
            
        if not message:
            return
            
        # Clear entry
        self.entry_var.set("")
        
        # Add user message to display
        self.add_message("You", message, message_type="user")
        
        # Show typing indicator
        self.update_status("Assistant is thinking...")
        
        # Process message in a thread to keep UI responsive
        threading.Thread(target=self._process_message, args=(message,), daemon=True).start()
        
    def _process_message(self, message):
        """Process message in background thread"""
        try:
            # Get response based on conversation state
            if self.awaiting_follow_up:
                # This is a response to a follow-up question
                response_data = self.bot.process_input(message)
            else:
                # This is a new query or continuation of conversation
                response_data = self.bot.process_input(message)
                
            # Update conversation tracking
            if 'conversation_id' in response_data and response_data['conversation_id']:
                self.current_conversation_id = response_data['conversation_id']
                self.conversation_id_var.set(f"Conversation: {self.current_conversation_id[:8]}...")
                self.conversation_active = True
            
            # Update awaiting_follow_up state
            self.awaiting_follow_up = (response_data.get('response_type') == 'follow_up_question')
            
            # Update conversation completion status
            if response_data.get('conversation_complete', False):
                self.awaiting_follow_up = False
                
            # Update status indicator
            if self.awaiting_follow_up:
                self.update_status("Waiting for your response...")
            else:
                self.update_status("")
                
            # Get the response text
            response = response_data.get('response', "Error processing your request.")
            
            # Determine message type based on response type
            response_type = response_data.get('response_type', 'final_response')
            
            # Add to chat based on response type
            if response_type == 'follow_up_question':
                self.add_message("Assistant", response, message_type="follow_up")
            elif response_type == 'safety_alert':
                self.add_message("Assistant", response, message_type="error")
            elif response_type == 'error':
                self.add_message("System", response, message_type="error")
            else:
                # Use typing animation for final responses
                self.typing_text = response
                self.typing_position = 0
                self.root.after(10, self._animate_typing)
                
        except Exception as e:
            # Log the error
            print(f"Error processing message: {str(e)}")
            
            # Display error to user
            self.add_message(
                "System",
                f"Error: {str(e)}\n\nPlease try asking your question in a different way.",
                message_type="error"
            )
            
            # Reset conversation state
            self.awaiting_follow_up = False
            self.update_status("")
            
    def _animate_typing(self):
        """Animate the typing of the assistant's response"""
        if not self.typing_text:
            return
            
        if self.typing_position == 0:
            # Start the message
            self.chat_display.config(state=tk.NORMAL)
            self.chat_display.insert(tk.END, "Assistant: ", "assistant")
            
        # Calculate how much to display in this frame
        chars_to_add = min(self.typing_speed, len(self.typing_text) - self.typing_position)
        
        if chars_to_add > 0:
            # Add next chunk of text
            next_text = self.typing_text[self.typing_position:self.typing_position + chars_to_add]
            
            # Check for disclaimer to apply special formatting
            if "Disclaimer:" in next_text:
                parts = next_text.split("Disclaimer:", 1)
                
                if parts[0]:
                    self.chat_display.config(state=tk.NORMAL)
                    self.chat_display.insert(tk.END, parts[0])
                    
                if len(parts) > 1:
                    self.chat_display.config(state=tk.NORMAL)
                    self.chat_display.insert(tk.END, "Disclaimer:", "disclaimer")
                    self.chat_display.insert(tk.END, parts[1], "disclaimer")
            else:
                # Normal text insertion
                self.chat_display.config(state=tk.NORMAL)
                self.chat_display.insert(tk.END, next_text)
                
            # Update position
            self.typing_position += chars_to_add
            
            # Scroll to bottom
            self.chat_display.see(tk.END)
            self.chat_display.config(state=tk.DISABLED)
            
            # Continue animation if not done
            if self.typing_position < len(self.typing_text):
                self.typing_animation = self.root.after(10, self._animate_typing)
            else:
                # End of message
                self.chat_display.config(state=tk.NORMAL)
                self.chat_display.insert(tk.END, "\n\n")
                self.chat_display.config(state=tk.DISABLED)
                self.chat_display.see(tk.END)
                
                # Reset typing state
                self.typing_text = ""
                self.typing_position = 0
                self.typing_animation = None
        else:
            # End of message
            self.chat_display.config(state=tk.NORMAL)
            self.chat_display.insert(tk.END, "\n\n")
            self.chat_display.config(state=tk.DISABLED)
            self.chat_display.see(tk.END)
            
            # Reset typing state
            self.typing_text = ""
            self.typing_position = 0
            self.typing_animation = None
            
    def update_status(self, status_text):
        """Update the conversation status indicator"""
        self.status_var.set(status_text)
        
    def add_message(self, sender, message, message_type="normal", error=False):
        self.chat_display.config(state=tk.NORMAL)
        
        # Determine tag based on message type or error flag
        if error:
            tag = "error"
            color = "#E74C3C"
        elif message_type == "user":
            tag = "user"
            color = "#2C3E50"
        elif message_type == "follow_up":
            tag = "follow_up"
            color = "#3498DB"
        elif message_type == "system":
            tag = "system"
            color = "#7F8C8D"
        else:
            tag = "normal"
            color = "#2C3E50"
            
        # Configure tags for different parts of the response
        self.chat_display.tag_config(tag, foreground=color)
        self.chat_display.tag_config("header", foreground="#3498DB", font=("Arial", 12, "bold"))
        self.chat_display.tag_config("section", foreground="#16A085", font=("Arial", 12, "bold"))
        self.chat_display.tag_config("disclaimer", foreground="#7F8C8D", font=("Arial", 10, "italic"))
        self.chat_display.tag_config("timestamp", foreground="#95A5A6", font=("Arial", 9, "italic"))
        # In the setup_ui method, add these text tags
        self.chat_display.tag_configure("user", foreground="#2C3E50", font=("Arial", 12, "bold"))
        self.chat_display.tag_configure("assistant", foreground="#27AE60", font=("Arial", 12, "bold"))
        self.chat_display.tag_configure("follow_up", foreground="#3498DB", font=("Arial", 12, "bold"))
        self.chat_display.tag_configure("error", foreground="#E74C3C", font=("Arial", 12))
        self.chat_display.tag_configure("system", foreground="#7F8C8D", font=("Arial", 10, "italic"))
        self.chat_display.tag_configure("disclaimer", foreground="#7F8C8D", font=("Arial", 10, "italic"))
        
        # Insert sender with appropriate tag
        self.chat_display.insert(tk.END, f"{sender}: ", tag)
        
        # Check if this is a formatted medical response
        if sender == "Assistant" and any(icon in message for icon in ["📋", "🔍", "🔎", "💊", "🛡️", "✅", "⚠️", "📝"]):
            # Split message into lines for section-based formatting
            lines = message.split("\n")
            for i, line in enumerate(lines):
                # Format section headers with emoji icons
                if re.match(r'^[📋🔍🔎💊🛡️✅⚠️📝]', line):
                    self.chat_display.insert(tk.END, f"\n{line}\n", "section")
                # Format disclaimer
                elif "Disclaimer:" in line:
                    self.chat_display.insert(tk.END, f"\n{line}\n", "disclaimer")
                # Format timestamp
                elif "Last Updated:" in line or "Information Last Updated:" in line:
                    self.chat_display.insert(tk.END, f"\n{line}\n", "timestamp")
                # Regular content
                else:
                    self.chat_display.insert(tk.END, f"{line}\n", tag)
        else:
            # Regular message format
            self.chat_display.insert(tk.END, f"{message}\n\n", tag)
        
        self.chat_display.config(state=tk.DISABLED)
        self.chat_display.see(tk.END)
                
    def clear_chat(self):
        """Clear the chat display and reset conversation state"""
        # Ask for confirmation
        self.chat_display.config(state=tk.NORMAL)
        self.chat_display.delete(1.0, tk.END)
        self.chat_display.config(state=tk.DISABLED)
        
        # Reset conversation state
        self.awaiting_follow_up = False
        self.update_status("")
        
    def start_new_conversation(self):
        """Start a new conversation and reset state"""
        # Reset conversation manager in the bot
        if hasattr(self.bot, 'conversation_manager'):
            self.bot.conversation_manager.reset_conversation()
            
        # Reset our tracking variables
        self.current_conversation_id = None
        self.awaiting_follow_up = False
        self.conversation_active = False
        
        # Update UI
        self.conversation_id_var.set("")
        self.update_status("New conversation started")
        
        # Add system message
        self.chat_display.config(state=tk.NORMAL)
        self.chat_display.insert(tk.END, "System: New conversation started.\n\n", "system")
        self.chat_display.config(state=tk.DISABLED)
        self.chat_display.see(tk.END)
        
    def use_example(self, example):
        """Use an example question"""
        self.entry_var.set(example)
        self.message_entry.config(fg="#2C3E50")
        self.send_message()

def main():
    """Main entry point for the application"""
    root = tk.Tk()
    app = MedicalChatApp(root)
    
    # Set window icon if available
    try:
        icon_path = Path(__file__).parent / "resources" / "icon.ico"
        if icon_path.exists():
            root.iconbitmap(icon_path)
    except Exception:
        pass  # Ignore icon loading errors
        
    # Center the window on screen
    window_width = 900
    window_height = 700
    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()
    center_x = int(screen_width/2 - window_width/2)
    center_y = int(screen_height/2 - window_height/2)
    root.geometry(f'{window_width}x{window_height}+{center_x}+{center_y}')
    
    # Start the GUI event loop
    root.mainloop()

if __name__ == "__main__":
    main()