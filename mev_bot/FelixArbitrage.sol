// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

import "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import "@openzeppelin/contracts/token/ERC20/utils/SafeERC20.sol";
import "@balancer-labs/v2-interfaces/contracts/vault/IVault.sol";

/**
 * @title FelixArbitrage
 * @dev Gas-optimized FELIX/WETH flash loan arbitrage contract
 * @notice Executes arbitrage between Uniswap V3 and PancakeSwap V3
 */
contract FelixArbitrage {
    using SafeERC20 for IERC20;

    // Constants
    address public constant WETH = 0x4200000000000000000000000000000000000006;
    address public constant FELIX = 0xf30Bf00edd0C22db54C9274B90D2A4C21FC09b07;
    address public constant BALANCER_VAULT = 0xBA12222222228d8Ba445958a75a0704d566BF2C8;
    
    // Uniswap V3 Router (Base)
    address public constant UNISWAP_ROUTER = 0x4752ba5dbc23f44d87826276bf6fd6b1c372ad24;
    
    // PancakeSwap V3 Router (Base)
    address public constant PANCAKESWAP_ROUTER = 0x1b81D678ffb9C0263b24A97847620C99d213eB14;
    
    // Owner
    address public owner;
    
    // Events
    event ArbitrageExecuted(
        uint256 ethAmount,
        uint256 felixReceived,
        uint256 ethReturned,
        uint256 profit,
        uint256 gasUsed
    );
    
    event FlashLoanReceived(uint256 amount);
    
    modifier onlyOwner() {
        require(msg.sender == owner, "Only owner");
        _;
    }
    
    constructor() {
        owner = msg.sender;
    }
    
    /**
     * @notice Execute arbitrage with flash loan
     * @param ethAmount Amount of ETH to borrow for arbitrage
     */
    function executeArbitrage(uint256 ethAmount) external onlyOwner {
        require(ethAmount > 0, "Amount must be > 0");
        
        // Prepare flash loan
        address[] memory tokens = new address[](1);
        tokens[0] = WETH;
        
        uint256[] memory amounts = new uint256[](1);
        amounts[0] = ethAmount;
        
        // Encode callback data
        bytes memory userData = abi.encode(ethAmount, msg.sender);
        
        // Execute flash loan
        IVault(BALANCER_VAULT).flashLoan(this, tokens, amounts, userData);
    }
    
    /**
     * @notice Flash loan callback function
     * @param tokens Tokens borrowed
     * @param amounts Amounts borrowed
     * @param feeAmounts Flash loan fees
     * @param userData Encoded callback data
     */
    function receiveFlashLoan(
        address[] memory tokens,
        uint256[] memory amounts,
        uint256[] memory feeAmounts,
        bytes memory userData
    ) external {
        require(msg.sender == BALANCER_VAULT, "Only Balancer vault");
        
        uint256 ethAmount = amounts[0];
        uint256 flashLoanFee = feeAmounts[0];
        address recipient = abi.decode(userData, (address));
        
        emit FlashLoanReceived(ethAmount);
        
        // Execute arbitrage swaps
        uint256 startGas = gasleft();
        
        // 1. Buy FELIX on Uniswap (lower price due to panic selling)
        uint256 felixAmount = _swapETHToFelix(ethAmount, UNISWAP_ROUTER);
        
        // 2. Sell FELIX on PancakeSwap (higher price)
        uint256 ethReturned = _swapFelixToETH(felixAmount, PANCAKESWAP_ROUTER);
        
        uint256 endGas = gasleft();
        uint256 gasUsed = startGas - endGas;
        
        // 3. Calculate profit
        uint256 totalOwed = ethAmount + flashLoanFee;
        require(ethReturned >= totalOwed, "Arbitrage not profitable");
        
        uint256 profit = ethReturned - totalOwed;
        
        // 4. Repay flash loan
        IERC20(WETH).safeTransfer(BALANCER_VAULT, totalOwed);
        
        // 5. Send profit to owner
        if (profit > 0) {
            IERC20(WETH).safeTransfer(owner, profit);
        }
        
        emit ArbitrageExecuted(ethAmount, felixAmount, ethReturned, profit, gasUsed);
    }
    
    /**
     * @notice Swap ETH to FELIX on specified DEX
     * @param ethAmount Amount of ETH to swap
     * @param router DEX router address
     * @return felixAmount Amount of FELIX received
     */
    function _swapETHToFelix(uint256 ethAmount, address router) internal returns (uint256 felixAmount) {
        // Approve router to spend WETH
        IERC20(WETH).safeApprove(router, ethAmount);
        
        // Exact input single swap
        bytes memory data = abi.encodeWithSelector(
            IUniswapV3Router.exactInputSingle.selector,
            IUniswapV3Router.ExactInputSingleParams({
                tokenIn: WETH,
                tokenOut: FELIX,
                fee: 3000, // 0.3% fee tier
                recipient: address(this),
                deadline: block.timestamp + 300,
                amountIn: ethAmount,
                amountOutMinimum: 0, // Accept any amount (for demo)
                sqrtPriceLimitX96: 0
            })
        );
        
        (bool success, bytes memory result) = router.call(data);
        require(success, "ETH to FELIX swap failed");
        
        felixAmount = abi.decode(result, (uint256));
        
        // Reset approval
        IERC20(WETH).safeApprove(router, 0);
    }
    
    /**
     * @notice Swap FELIX to ETH on specified DEX
     * @param felixAmount Amount of FELIX to swap
     * @param router DEX router address
     * @return ethAmount Amount of ETH received
     */
    function _swapFelixToETH(uint256 felixAmount, address router) internal returns (uint256 ethAmount) {
        // Approve router to spend FELIX
        IERC20(FELIX).safeApprove(router, felixAmount);
        
        // Exact input single swap
        bytes memory data = abi.encodeWithSelector(
            IUniswapV3Router.exactInputSingle.selector,
            IUniswapV3Router.ExactInputSingleParams({
                tokenIn: FELIX,
                tokenOut: WETH,
                fee: 3000, // 0.3% fee tier
                recipient: address(this),
                deadline: block.timestamp + 300,
                amountIn: felixAmount,
                amountOutMinimum: 0, // Accept any amount (for demo)
                sqrtPriceLimitX96: 0
            })
        );
        
        (bool success, bytes memory result) = router.call(data);
        require(success, "FELIX to ETH swap failed");
        
        ethAmount = abi.decode(result, (uint256));
        
        // Reset approval
        IERC20(FELIX).safeApprove(router, 0);
    }
    
    /**
     * @notice Emergency withdraw tokens
     * @param token Token address
     * @param amount Amount to withdraw
     */
    function emergencyWithdraw(address token, uint256 amount) external onlyOwner {
        IERC20(token).safeTransfer(owner, amount);
    }
    
    /**
     * @notice Get current WETH balance
     */
    function getWETHBalance() external view returns (uint256) {
        return IERC20(WETH).balanceOf(address(this));
    }
    
    /**
     * @notice Get current FELIX balance
     */
    function getFELIXBalance() external view returns (uint256) {
        return IERC20(FELIX).balanceOf(address(this));
    }
    
    /**
     * @notice Transfer ownership
     */
    function transferOwnership(address newOwner) external onlyOwner {
        owner = newOwner;
    }
}

/**
 * @notice Interface for Uniswap V3 Router
 */
interface IUniswapV3Router {
    struct ExactInputSingleParams {
        address tokenIn;
        address tokenOut;
        uint24 fee;
        address recipient;
        uint256 deadline;
        uint256 amountIn;
        uint256 amountOutMinimum;
        uint160 sqrtPriceLimitX96;
    }
    
    function exactInputSingle(ExactInputSingleParams calldata params) external payable returns (uint256 amountOut);
}
