const path = require("path");
const fs = require("fs");

const jsDir = path.resolve(__dirname, "js");
const entry = fs
  .readdirSync(jsDir)
  .filter((file) => file.endsWith(".ts"))
  .reduce((entries, file) => {
    const name = path.basename(file, ".ts");
    entries[name] = path.join(jsDir, file);
    return entries;
  }, {});

module.exports = {
  mode: "production",
  entry,
  output: {
    filename: "[name].js",
    path: path.resolve(__dirname, "..", "app", "static", "js"),
  },
  resolve: {
    extensions: [".ts", ".js"],
    modules: [path.resolve(__dirname, "js"), "node_modules"],
    alias: {
      "@": path.resolve(__dirname, "js"),
    },
  },
  module: {
    rules: [
      {
        test: /\.ts$/,
        use: "ts-loader",
        exclude: /node_modules/,
      },
    ],
  },
  optimization: {
    minimize: true,
  },
  watchOptions: {
    ignored: /node_modules/,
  },
};
