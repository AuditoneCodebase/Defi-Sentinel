document.addEventListener("DOMContentLoaded", function () {
    console.log("JavaScript loaded successfully!");

    let web3;
    let userAddress;
    const BASE_CHAIN_ID = "0x2105"; // Base Mainnet Chain ID (8453 in hex)
    const BASE_RPC_URL = "https://mainnet.base.org";
    const BASE_EXPLORER_URL = "https://basescan.org/";

    const connectWalletButton = document.getElementById("connectWallet");

    if (!connectWalletButton) {
        console.error("Connect Wallet button not found!");
    } else {
        connectWalletButton.addEventListener("click", async () => {
            console.log("Connect Wallet button clicked.");
            await connectWallet();
        });
    }

    async function connectWallet() {
        if (window.ethereum) {
            web3 = new Web3(window.ethereum);
            try {
                await window.ethereum.request({ method: "eth_requestAccounts" });
                userAddress = (await web3.eth.getAccounts())[0];
                document.getElementById("walletAddress").innerText = `Connected: ${userAddress}`;
                console.log(`Wallet Connected: ${userAddress}`);

                // Ensure user is on Base Network
                await checkAndSwitchNetwork();
                document.getElementById("fetchHoldings").classList.remove("hidden");
            } catch (error) {
                console.error("Error connecting wallet:", error);
                alert("Failed to connect wallet.");
            }
        } else {
            alert("MetaMask not detected. Please install it.");
        }
    }

    async function checkAndSwitchNetwork() {
        const chainId = await web3.eth.getChainId();
        console.log(`Current Chain ID: ${chainId}`);

        if (chainId !== parseInt(BASE_CHAIN_ID, 16)) {
            try {
                await window.ethereum.request({
                    method: "wallet_switchEthereumChain",
                    params: [{ chainId: BASE_CHAIN_ID }]
                });
                alert("Switched to Base Network ✅");
            } catch (error) {
                console.error("Error switching network:", error);
                if (error.code === 4902) {
                    await addBaseNetwork();
                } else {
                    alert("You must be on Base Network to use this app.");
                }
            }
        }
    }

    async function addBaseNetwork() {
        try {
            await window.ethereum.request({
                method: "wallet_addEthereumChain",
                params: [{
                    chainId: BASE_CHAIN_ID,
                    chainName: "Base Mainnet",
                    nativeCurrency: { name: "ETH", symbol: "ETH", decimals: 18 },
                    rpcUrls: [BASE_RPC_URL],
                    blockExplorerUrls: [BASE_EXPLORER_URL]
                }]
            });
            alert("Base Network added. Please switch to Base to continue.");
        } catch (error) {
            console.error("Error adding Base Network:", error);
            alert("Failed to add Base Network. Please switch manually.");
        }
    }
});
