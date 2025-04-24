const logger = {
    debug: (...args) => {
        if (process.env.NODE_ENV !== 'production') {
            console.debug('[Debug]:', ...args);
        }
    },
    info: (...args) => {
        if (process.env.NODE_ENV !== 'production') {
            console.info('[Info]:', ...args);
        }
    },
    warn: (...args) => {
        console.warn('[Warning]:', ...args);
    },
    error: (...args) => {
        console.error('[Error]:', ...args);
    }
};

export default logger;