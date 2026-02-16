// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

import "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import "@openzeppelin/contracts/token/ERC20/utils/SafeERC20.sol";
import "@balancer-labs/v2-interfaces/contracts/vault/IVault.sol";

/**
 * @title MinimalFelixArbitrage
 * @dev Ultra gas-optimized FELIX arbitrage
 * @notice Minimal deployment cost, maximum profit
 */
contract MinimalFelixArbitrage {
    using SafeERC20 for IERC20;

    // Constants
    address public constant WETH = 0x4200000000000000000000000000000000000006;
    address public constant FELIX = 0xf30Bf00edd0C22db54C9274B90D2A4C21FC09b07;
    address public constant BALANCER_VAULT = 0xBA12222222228d8Ba445958a75a0704d566BF2C8;
    address public constant UNISWAP_ROUTER = 0x4752ba5dbc23f44d87826276bf6fd6b1c372ad24;
    address public constant AERODROME_ROUTER = 0xcF77a3Ba9A5CA399B7C97c7a1C7F6f1a4F79D2F8;
    
    address public owner;
    
    event ArbitrageExecuted(uint256 profit);
    
    modifier onlyOwner() {
        require(msg.sender == owner, "Only owner");
        _;
    }
    
    constructor() {
        owner = msg.sender;
    }
    
    function executeArbitrage(uint256 ethAmount) external onlyOwner {
        address[] memory tokens = new address[](1);
        tokens[0] = WETH;
        
        uint256[] memory amounts = new uint256[](1);
        amounts[0] = ethAmount;
        
        bytes memory userData = abi.encode(ethAmount);
        
        IVault(BALANCER_VAULT).flashLoan(this, tokens, amounts, userData);
    }
    
    function receiveFlashLoan(
        address[] memory,
        uint256[] memory amounts,
        uint256[] memory feeAmounts,
        bytes memory userData
    ) external {
        require(msg.sender == BALANCER_VAULT, "Only vault");
        
        uint256 ethAmount = amounts[0];
        uint256 fee = feeAmounts[0];
        
        // Buy FELIX on Uniswap (cheaper)
        uint256 felixAmount = _swap(UNISWAP_ROUTER, WETH, FELIX, ethAmount);
        
        // Sell FELIX on Aerodrome (expensive)
        uint256 ethReturned = _swap(AERODROME_ROUTER, FELIX, WETH, felixAmount);
        
        // Repay loan
        uint256 totalOwed = ethAmount + fee;
        require(ethReturned >= totalOwed, "Not profitable");
        
        IERC20(WETH).safeTransfer(BALANCER_VAULT, totalOwed);
        
        uint256 profit = ethReturned - totalOwed;
        if (profit > 0) {
            IERC20(WETH).safeTransfer(owner, profit);
        }
        
        emit ArbitrageExecuted(profit);
    }
    
    function _swap(address router, address tokenIn, address tokenOut, uint256 amountIn) 
        internal 
        returns (uint256 amountOut) 
    {
        IERC20(tokenIn).safeApprove(router, amountIn);
        
        (bool success, bytes memory result) = router.call(
            abi.encodeWithSignature(
                "exactInputSingle((address,address,uint24,address,uint256,uint256,uint256,uint160))",
                tokenIn,
                tokenOut,
                uint24(3000),
                address(this),
                block.timestamp + 300,
                amountIn,
                uint256(0),
                uint160(0)
            )
        );
        
        require(success, "Swap failed");
        amountOut = abi.decode(result, (uint256));
        IERC20(tokenIn).safeApprove(router, 0);
    }
}
