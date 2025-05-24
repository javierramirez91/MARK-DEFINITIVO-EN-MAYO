// Importamos la función para comunicarnos con Claude
const { askClaude } = require('./claude-integration');
// Importamos el módulo fs con promesas
const fs = require('fs').promises;
// Para leer directorios y archivos
const path = require('path');

/**
 * Función principal que ejecuta las tareas en cascada
 */
async function runCascade() {
  try {
    console.log("Iniciando automatización en cascada con Claude...");
    
    // Paso 1: Analizar el código actual
    console.log("Paso 1: Analizando el código del proyecto...");
    const files = await getProjectFiles();
    
    if (files.length === 0) {
      console.log("No se encontraron archivos para analizar.");
      return;
    }
    
    const fileContents = await readFilesContent(files.slice(0, 3)); // Limitamos a 3 archivos por simplicidad
    const codeAnalysis = await askClaude(`Analiza este código y describe su estructura y propósito: \n\n${fileContents.join('\n\n===NUEVO ARCHIVO===\n\n')}`);
    await fs.writeFile('code-analysis.md', codeAnalysis);
    console.log("✅ Análisis de código completado y guardado en 'code-analysis.md'");
    
    // Paso 2: Generar pruebas para el primer archivo
    if (fileContents.length > 0) {
      console.log("Paso 2: Generando pruebas unitarias...");
      const testCode = await askClaude(`Genera pruebas unitarias para este código JavaScript: \n\n${fileContents[0]}`);
      await fs.writeFile('test-suite.js', testCode);
      console.log("✅ Pruebas unitarias generadas y guardadas en 'test-suite.js'");
    }
    
    // Paso 3: Sugerir mejoras de código
    console.log("Paso 3: Identificando posibles mejoras...");
    const improvements = await askClaude(`Sugiere mejoras para este código en términos de rendimiento, seguridad y legibilidad: \n\n${fileContents.join('\n\n===NUEVO ARCHIVO===\n\n')}`);
    await fs.writeFile('suggested-improvements.md', improvements);
    console.log("✅ Sugerencias de mejora generadas y guardadas en 'suggested-improvements.md'");
    
    console.log("\n🎉 Automatización en cascada completada con éxito");
  } catch (error) {
    console.error("❌ Error en la automatización:", error);
  }
}

/**
 * Función para obtener la lista de archivos de código en el proyecto
 * @returns {Promise<string[]>} - Lista de rutas de archivos
 */
async function getProjectFiles() {
  try {
    const files = [];
    const dirContent = await fs.readdir('./');
    
    for (const item of dirContent) {
      const stats = await fs.stat(item);
      
      if (stats.isFile() && 
         (item.endsWith('.js') || item.endsWith('.ts') || item.endsWith('.jsx') || item.endsWith('.tsx'))) {
        files.push(item);
      }
    }
    
    return files;
  } catch (error) {
    console.error("Error al leer los archivos del proyecto:", error);
    return [];
  }
}

/**
 * Función para leer el contenido de los archivos
 * @param {string[]} files - Lista de archivos a leer
 * @returns {Promise<string[]>} - Contenido de los archivos
 */
async function readFilesContent(files) {
  const contents = [];
  
  for (const file of files) {
    try {
      const content = await fs.readFile(file, 'utf8');
      contents.push(`Archivo: ${file}\n\n${content}`);
    } catch (error) {
      console.error(`Error al leer el archivo ${file}:`, error);
    }
  }
  
  return contents;
}

// Ejecutamos la cascada de automatización
runCascade();