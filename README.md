# Python and React AI Assistant Application

This application is an AI-powered assistant that integrates Python execution capabilities with React component rendering on the fly, offering a comprehensive environment for data analysis, visualization, and interactive web development.

## Key Features and Functionalities

1. **Intelligent Chat Interface**: 
   - Powered by Claude 3.5 Sonnet, an advanced AI model from Anthropic.
   - Enables natural language interactions for task requests and queries.

2. **Python Code Execution**: 
   - Runs Python code within a secure Jupyter notebook environment.
   - Executes data analysis tasks using popular libraries.
   - Displays code results directly in the chat interface.

3. **Dynamic React Component Creation**:
   - Generates and renders React components on-demand.
   - Allows real-time preview of created components.

4. **Integrated File Operations**: 
   - Facilitates file uploads for AI processing.
   - Enables downloads of AI-generated files.
   - Manages files within the application environment.

5. **Advanced Data Visualization**: 
   - Creates diverse charts and graphs using matplotlib and other libraries.
   - Presents data visually to enhance understanding and analysis.

6. **LangGraph-based Workflow**: 
   - Orchestrates AI decision-making processes.
   - Provides a real-time Mermaid diagram of the workflow in the sidebar.

7. **Intuitive Streamlit Interface**: 
   - Offers a clean, user-friendly interface for seamless interaction.

8. **Adaptive Tool Utilization**: 
   - Switches between various functionalities (Python, React, file operations) based on context.

9. **Flexible Package Management**: 
   - Supports installation of additional Python packages as required.

10. **Web Resource Access**: 
    - Capable of making API requests and accessing online information.

11. **Robust Error Handling**: 
    - Delivers clear error messages and explanations for troubleshooting.

## Setup and Usage

### Python Dependency Installation

Before running the application, ensure you have configured the necessary API keys in the `.env` file located at the root of the project directory. Follow these steps for Python dependency installation:

1. Create a virtual environment by running:
   ```sh
   python -m venv venv
   ```
   This command creates a new directory named `venv` in your project directory, which will contain the Python executable and libraries.

2. Activate the virtual environment:
   - On Windows, run:
     ```cmd
     .\venv\Scripts\activate
     ```
   - On macOS and Linux, run:
     ```sh
     source venv/bin/activate
     ```
   After activation, your terminal prompt will change to indicate that the virtual environment is active.

3. With the virtual environment activated, install the required Python packages by running:
   ```sh
   pip install -r requirements.txt
   ```
   This command reads the `requirements.txt` file and installs all the listed packages along with their dependencies.

Remember to activate the virtual environment (`venv`) every time you work on this project. To deactivate the virtual environment and return to your global Python environment, simply run `deactivate`.

### Node.js Package Installation and Build

After setting up the Python environment, proceed with the Node.js setup:

1. Install the required Node.js packages:
   ```sh
   npm install
   ```

2. Build the packages:
   ```sh
   npm run build
   ```

### Starting the Application

Finally, to start the application:

1. Launch the Streamlit application:
   ```sh
   streamlit run main.py
   ```

2. Access the application via your web browser to start interacting with the AI assistant.

Note: The application automatically initiates the React development server in a subprocess, eliminating the need to manually run `npm start`.

## Important Note

This application combines advanced AI capabilities with code execution. Always review and understand any code before execution, particularly in production environments.