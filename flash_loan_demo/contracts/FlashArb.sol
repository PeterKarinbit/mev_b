// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/token/ERC20/IERC20.sol";

interface IBalancerVault {
    function flashLoan(address recipient, address[] memory tokens, uint256[] memory amounts, bytes memory userData) external;
}

interface IFlashLoanRecipient {
    function receiveFlashLoan(
        address[] memory tokens,
        uint256[] memory amounts,
        uint256[] memory feeAmounts,
        bytes memory userData
    ) external;
}

interface IAerodromeRouter {
    struct Route { address from; address to; bool stable; address factory; }
    function swapExactTokensForTokens(uint256 amountIn, uint256 amountOutMin, Route[] calldata routes, address to, uint256 deadline) external returns (uint256[] memory amounts);
}

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

contract FlashArb is IFlashLoanRecipient {
    address private constant BALANCER_VAULT = 0xBA12222222228d8Ba445958a75a0704d566BF2C8;
    address private constant WETH = 0x4200000000000000000000000000000000000006;
    address private constant AERO_ROUTER = 0xCf77A3bA9A5ca399Af7227c093A13010aD0743f8;
    address private constant UNI_V3_ROUTER = 0x26213694015609b505F04291886134D60bbeDc37;
    address private constant PANCAKE_ROUTER = 0x1B8134a47B7675D6666cc20ec89ca564706F5A07;
    address public owner;

    constructor() { owner = msg.sender; }

    // Matches your NEW bot signature: execute(address, uint256, bytes)
    function execute(address asset, uint256 amount, bytes calldata params) external {
        require(msg.sender == owner, "Only owner");
        
        address[] memory tokens = new address[](1);
        tokens[0] = asset; // Should be WETH
        uint256[] memory amounts = new uint256[](1);
        amounts[0] = amount;

        // The userData MUST contain everything needed for the callback
        IBalancerVault(BALANCER_VAULT).flashLoan(
            address(this),
            tokens,
            amounts,
            params // Pass your encoded params (isBuyFirst, tokenB, fee1, fee2)
        );
    }

    // Standard Balancer V2 Callback
    function receiveFlashLoan(
        address[] memory tokens,
        uint256[] memory amounts,
        uint256[] memory feeAmounts,
        bytes memory userData
    ) external override {
        require(msg.sender == BALANCER_VAULT, "Only vault");
        
        address loanToken = tokens[0];
        uint256 loanAmount = amounts[0];
        
        // Decode your bot's params
        (bool isBuyFirst, address tokenB, uint24 fee1, uint24 fee2) = abi.decode(userData, (bool, address, uint24, uint24));

        uint256 currentBalance = loanAmount;

        // Logic to determine MODE based on the fees passed (Mode logic simplified for V5.0)
        // This handles Aero (0 fee), Uni (fee1), Pan (fee2)
        
        if (fee1 > 0 && fee2 > 0) { // Uni <-> Pan
            currentBalance = _swapUniV3(isBuyFirst ? WETH : tokenB, isBuyFirst ? tokenB : WETH, fee1, currentBalance, UNI_V3_ROUTER);
            currentBalance = _swapUniV3(isBuyFirst ? tokenB : WETH, isBuyFirst ? WETH : tokenB, fee2, currentBalance, PANCAKE_ROUTER);
        } else if (fee1 == 0 && fee2 > 0) { // Aero <-> Pan
            if (isBuyFirst) {
                currentBalance = _swapAero(WETH, tokenB, currentBalance);
                currentBalance = _swapUniV3(tokenB, WETH, fee2, currentBalance, PANCAKE_ROUTER);
            } else {
                currentBalance = _swapUniV3(WETH, tokenB, fee2, currentBalance, PANCAKE_ROUTER);
                currentBalance = _swapAero(tokenB, WETH, currentBalance);
            }
        } else { // Aero <-> Uni
            if (isBuyFirst) {
                currentBalance = _swapAero(WETH, tokenB, currentBalance);
                currentBalance = _swapUniV3(tokenB, WETH, fee1, currentBalance, UNI_V3_ROUTER);
            } else {
                currentBalance = _swapUniV3(WETH, tokenB, fee1, currentBalance, UNI_V3_ROUTER);
                currentBalance = _swapAero(tokenB, WETH, currentBalance);
            }
        }

        // Must show profit + cover Balancer fees (0 on Base currently)
        require(currentBalance > loanAmount + feeAmounts[0], "No profit");

        // Repay the loan
        IERC20(loanToken).transfer(BALANCER_VAULT, loanAmount + feeAmounts[0]);
        // Keep the profit in the contract for owner withdrawal
    }

    function _swapUniV3(address tokenIn, address tokenOut, uint24 fee, uint256 amountIn, address router) internal returns (uint256) {
        IERC20(tokenIn).approve(router, amountIn);
        return IUniswapV3Router(router).exactInputSingle(
            IUniswapV3Router.ExactInputSingleParams({
                tokenIn: tokenIn,
                tokenOut: tokenOut,
                fee: fee,
                recipient: address(this),
                deadline: block.timestamp + 60,
                amountIn: amountIn,
                amountOutMinimum: 0,
                sqrtPriceLimitX96: 0
            })
        );
    }

    function _swapAero(address tokenIn, address tokenOut, uint256 amountIn) internal returns (uint256) {
        IERC20(tokenIn).approve(AERO_ROUTER, amountIn);
        IAerodromeRouter.Route[] memory routes = new IAerodromeRouter.Route[](1);
        routes[0] = IAerodromeRouter.Route({ from: tokenIn, to: tokenOut, stable: false, factory: 0x420DD381b31aEf6683db6B902084cB0FFECe40Da });
        uint256[] memory amountsResult = IAerodromeRouter(AERO_ROUTER).swapExactTokensForTokens(amountIn, 0, routes, address(this), block.timestamp + 60);
        return amountsResult[amountsResult.length - 1];
    }

    function withdraw(address token) external {
        require(msg.sender == owner);
        IERC20(token).transfer(owner, IERC20(token).balanceOf(address(this)));
    }
}
