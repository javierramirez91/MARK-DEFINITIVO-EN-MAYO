// Importamos la función que creamos anteriormente
const { askClaude } = require('./claude-integration');

// Función asíncrona para probar la conexión con Claude
async function testClaudeConnection() {
  console.log("Probando conexión con Claude API...");
  
  try {
    // Enviamos una pregunta simple a Claude
    const response = await askClaude("Hola Claude, ¿me puedes ayudar a escribir código en JavaScript?");
    
    // Mostramos la respuesta
    console.log("Respuesta de Claude:");
    console.log("-------------------");
    console.log(response);
    console.log("-------------------");
    console.log("¡Conexión exitosa!");
  } catch (error) {
    console.error("Error al conectar con Claude:", error);
  }
}

// Ejecutamos la función de prueba
testClaudeConnection();