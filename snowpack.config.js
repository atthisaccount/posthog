const proxy = require('http2-proxy')

module.exports = {
    exclude: [
        '**/*.stories.*',
        '**/*.test.*',
        '**/*.cy-spec.*',
        '**/*Type.*',
        '**/frontend/src/test/**',
        '**/frontend/src/mocks/**',
    ],
    mount: {
        'frontend/snowpack': { url: '/', static: true },
        'frontend/public': { url: '/static', static: true },
        'frontend/src': { url: '/dist' },
    },
    routes: [
        {
            match: 'all',
            src: '/api/.*',
            dest: (req, res) => {
                return proxy.web(req, res, {
                    hostname: 'localhost',
                    port: 8000,
                })
            },
        },
        {
            match: 'routes',
            src: '.*',
            dest: '/index.html',
        },
    ],
    alias: {
        '~': './frontend/src',
        lib: './frontend/src/lib',
        scenes: './frontend/src/scenes',
        public: './frontend/public',
        // 'dayjs-es/plugin/timezone': 'dayjs/plugin/timezone',
        // dayjs: 'dayjs-es',
        json2mq: './frontend/json2mq.js',
    },

    plugins: [
        '@snowpack/plugin-react-refresh',
        '@snowpack/plugin-babel',
        '@snowpack/plugin-dotenv',
        '@snowpack/plugin-typescript',
        '@snowpack/plugin-postcss',
    ],
    devOptions: {},
    packageOptions: {
        external: [
            'dayjs',
            'posthog-js-lite',
            'kea-loaders',
            'json2mq',
            'warning',
            'react-syntax-highlighter',
            'copy-to-clipboard',
        ],
        polyfillNode: true,
        knownEntrypoints: [
            '@babel/runtime/helpers/asyncToGenerator',
            '@babel/runtime/helpers/extends',
            'rc-slider',
            'rc-tooltip/es/placements',
            'rc-util/es/Children/toArray',
            'rc-util/es/Dom/addEventListener',
            'rc-util/es/Dom/canUseDom',
            'rc-util/es/Dom/contains',
            'rc-util/es/Dom/css',
            'rc-util/es/Dom/findDOMNode',
            'rc-util/es/Dom/isVisible',
            'rc-util/es/KeyCode',
            'rc-util/es/Portal',
            'rc-util/es/PortalWrapper',
            'rc-util/es/createChainedFunction',
            'rc-util/es/getScrollBarSize',
            'rc-util/es/hooks/useMemo',
            'rc-util/es/hooks/useMergedState',
            'rc-util/es/isMobile',
            'rc-util/es/omit',
            'rc-util/es/pickAttrs',
            'rc-util/es/raf',
            'rc-util/es/ref',
            'rc-util/es/utils/get',
            'rc-util/es/utils/set',
            'rc-util/es/warning',
            'react-transition-group',
            'string-convert/camel2hyphen',
        ],
    },
}