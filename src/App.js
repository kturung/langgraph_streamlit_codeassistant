import React from 'react';

function App() {
  return (
    <div className="min-h-screen flex flex-col bg-gray-100">
      <header className="bg-blue-600 text-white p-4">
        <h1 className="text-2xl font-bold">My React App</h1>
      </header>
      
      <main className="flex-grow container mx-auto px-4 py-8">
        <h2 className="text-xl font-semibold mb-4">Welcome to My React App</h2>
        <p className="mb-4">This is a basic React application styled with Tailwind CSS.</p>
        <button className="bg-green-500 hover:bg-green-600 text-white font-bold py-2 px-4 rounded">
          Click me!
        </button>
      </main>
      
      <footer className="bg-gray-200 p-4 text-center">
        <p>&copy; 2023 My React App. All rights reserved.</p>
      </footer>
    </div>
  );
}

export default App;