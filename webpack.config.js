const path = require('path');

module.exports = {
    entry: './frontend.js',
    output: {
        path: path.resolve(__dirname, 'static/js'),
        filename: 'frontend.js',
    },
    module: {
        rules: [
            {
                test: /\.js$/,
                exclude: /node_modules/,
                use: {
                    loader: 'babel-loader',
                    options: {
                        presets: ['@babel/preset-env', '@babel/preset-react'],
                    },
                },
            },
        ],
    },
    mode: 'production',
};
