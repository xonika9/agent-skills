export type Fields = Record<string, unknown>;

export type Logger = {
  info: (msg: string, fields?: Fields) => void;
  warn: (msg: string, fields?: Fields) => void;
  error: (msg: string, fields?: Fields) => void;
  child: (fields: Fields) => Logger;
};

// One JSON object per line on stdout. Never pass secrets or personal data.
export function createLogger(base: Fields = {}): Logger {
  const write = (level: string, msg: string, fields?: Fields) =>
    console.log(JSON.stringify({ time: new Date().toISOString(), level, msg, ...base, ...fields }));
  return {
    info: (msg, fields) => write("info", msg, fields),
    warn: (msg, fields) => write("warn", msg, fields),
    error: (msg, fields) => write("error", msg, fields),
    child: (fields) => createLogger({ ...base, ...fields }),
  };
}

export const silentLogger: Logger = {
  info: () => {},
  warn: () => {},
  error: () => {},
  child: () => silentLogger,
};
