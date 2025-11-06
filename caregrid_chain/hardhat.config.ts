import { HardhatUserConfig } from "hardhat/config";
require("@nomicfoundation/hardhat-toolbox");
require('dotenv').config();

// Prefer explicit SEPOLIA_RPC_URL if provided. Otherwise fall back to INFURA_API_KEY.
const SEPOLIA_RPC_URL = process.env.SEPOLIA_RPC_URL && process.env.SEPOLIA_RPC_URL.length > 0
  ? process.env.SEPOLIA_RPC_URL
  : (process.env.INFURA_API_KEY ? `https://sepolia.infura.io/v3/${process.env.INFURA_API_KEY}` : "");

// Normalize private key: allow with or without 0x prefix
const RAW_PRIVATE_KEY = process.env.PRIVATE_KEY || "";
const PRIVATE_KEY = RAW_PRIVATE_KEY
  ? (RAW_PRIVATE_KEY.startsWith('0x') ? RAW_PRIVATE_KEY : `0x${RAW_PRIVATE_KEY}`)
  : undefined;

if (!SEPOLIA_RPC_URL) {
  console.warn("Warning: SEPOLIA RPC URL is empty. Set SEPOLIA_RPC_URL or INFURA_API_KEY in .env to deploy to Sepolia.");
}

const config: HardhatUserConfig = {
  solidity: "0.8.28",
  paths: {
    sources: "./contracts",
    tests: "./test",
    cache: "./cache",
    artifacts: "./artifacts"
  },
  networks: {
    sepolia: {
      url: SEPOLIA_RPC_URL,
      accounts: PRIVATE_KEY ? [PRIVATE_KEY] : [],
    },
    localhost: {
      url: "http://127.0.0.1:8545"
    }
  },
};

module.exports = config;