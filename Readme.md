#all current work is on main branch not master

# Memory Project

The Memory Project is an experimental endeavor aiming to revolutionize how we capture, process, and recall information from daily interactions. By leveraging cutting-edge artificial intelligence and audio processing technologies, the project aspires to create a seamless system for summarizing conversations, answering contextual queries, and integrating with wearable devices.

## Vision

Imagine a world where you no longer need to take notes in meetings or struggle to remember the finer details of a conversation. The Memory Project seeks to make this vision a reality by building a system that records audio, transcribes speech, identifies speakers, and uses AI to summarize and make the information accessible.

## Current Status

This project is in its **early experimental stages**. The codebase serves as a testing ground for various technologies and approaches, with no fully functional product yet. Key activities include:

- Exploring audio diarization and transcription methods.
- Prototyping workflows for integrating transcriptions with AI language models.
- Testing the feasibility of running these systems on portable or low-power devices.

## Tools and Technologies

The project employs a wide range of tools and libraries to experiment with various components. Below is a list of the tools currently being used:

### Audio Processing
- **Azure Cognitive Services Speech SDK**: For audio transcription and speaker diarization.
- **Pydub**: For audio file manipulation, such as conversion and compression.
- **FFmpeg**: Used for aggressive audio compression in experiments.

### AI and Machine Learning
- **OpenAI API**: Provides language model capabilities for text understanding and response generation.
- **Venice AI**: Integrates conversational AI for enhanced user interactions.
- **PyTorch**: Supports deep learning experiments and CUDA-based computations.

### Data Management
- **SQLite**: Stores transcription data for structured querying and retrieval.
- **CSV Utilities**: For importing and exporting data during the prototyping phase.

### System Compatibility
- **CUDA Toolkit**: Ensures compatibility with GPU acceleration for faster processing.
- **Hugging Face SDK**: Allows experimentation with pre-trained diarization and transcription models.

## Goals

1. **Ease of Recall**:
   - Develop a system capable of answering questions like, "What was discussed in my last meeting?" or "What did I talk about with my client yesterday?"

2. **Wearable Integration**:
   - Enable recording and processing through wearable devices, such as body cameras or microphones, making the system discreet and easy to use.

3. **Offline Functionality**:
   - Ensure the system can work without constant internet connectivity, using devices like Raspberry Pi or similar hardware for localized processing.

4. **Data Privacy**:
   - Keep user data secure and ensure that recordings and transcriptions are only accessible to the user.

## Use Cases

- **Professional Settings**:
  - Automate meeting summaries and ensure accurate records of discussions.
  
- **Personal Productivity**:
  - Keep track of daily interactions without the need for manual notes.
  
- **Accessibility**:
  - Help individuals with memory challenges or disabilities by providing a reliable system for recall.

## Acknowledgments

The Memory Project builds upon open-source tools, such as Azure Cognitive Services, PyTorch, and Hugging Face, as well as APIs from platforms like OpenAI and Venice AI.

## Contributing

This is an exploratory project, and contributions are welcome. If you have expertise in audio processing, machine learning, or wearable technology, feel free to reach out or fork the repository.

---
