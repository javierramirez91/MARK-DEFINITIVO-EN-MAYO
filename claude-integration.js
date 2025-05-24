// Cargamos las variables de entorno desde el archivo .env
require('dotenv').config();
// Importamos axios para hacer peticiones HTTP
const axios = require('axios');

/**
 * Función para enviar preguntas a Claude y obtener respuestas
 * @param {string} prompt - La pregunta o instrucción para Claude
 * @returns {Promise<string>} - La respuesta de Claude
 */
async function askClaude(prompt) {
  try {
    // Hacemos una petición POST a la API de Claude
    const response = await axios.post(
      'https://api.anthropic.com/v1/messages',
      {
        // Especificamos el modelo de Claude a usar
        model: "claude-3-7-sonnet-20250219",
        // Número máximo de tokens en la respuesta
        max_tokens: 1024,
        // El mensaje que enviamos a Claude
        messages: [
          { role: "user", content: prompt }
        ]
      },
      {
        // Cabeceras necesarias para la API
        headers: {
          'Content-Type': 'application/json',
          'x-api-key': process.env.CLAUDE_API_KEY,
          'anthropic-version': '2023-06-01'
        }
      }
    );
    
    // Extraemos el texto de la respuesta
    return response.data.content[0].text;
  } catch (error) {
    // Manejamos cualquier error que pueda ocurrir
    console.error('Error al comunicarse con Claude:', error.response?.data || error.message);
    return null;
  }
}

// Exportamos la función para usarla en otros archivos
module.exports = { askClaude };