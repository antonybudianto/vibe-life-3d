import { fileURLToPath } from 'node:url';

// Vinext beta.5 forces process.exit(0) while native Vite handles are closing.
// Let Windows drain those handles naturally; keep every failure exit unchanged.
if (process.platform === 'win32') {
  const exit = process.exit.bind(process);
  process.exit = (code) => {
    if (Number(code ?? 0) === 0) { process.exitCode = 0; return; }
    exit(code);
  };
}

const cli = new URL('cli.js', import.meta.resolve('vinext'));
process.argv = [process.execPath, fileURLToPath(cli), 'build', ...process.argv.slice(2)];
await import(cli.href);
