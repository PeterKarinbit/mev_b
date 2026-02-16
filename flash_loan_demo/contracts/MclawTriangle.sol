
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

interface IERC20 {
    function balanceOf(address account) external view returns (uint256);
    function transfer(address recipient, uint256 amount) external returns (bool);
    function approve(address spender, uint256 amount) external returns (bool);
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

interface IMorpho {
    function flashLoan(address token, uint256 amount, bytes calldata data) external;
}

contract MclawTriangle {
    address constant WETH = 0x4200000000000000000000000000000000000006;
    address constant UNI_V3 = 0x2626664c2603336E57B271c5C0b26F421741e481;
    address constant MORPHO = 0xBBBBBbbBBb9cC5e90e3b3Af64bdAF62C37EEFFCb;

    address public immutable owner;

    constructor() {
        owner = msg.sender;
        IERC20(WETH).approve(UNI_V3, type(uint256).max);
    }

    struct TriangleParams {
        address[] tokens;
        uint24[] fees;
        uint256 amount;
    }

    function execute(address[] calldata tokens, uint24[] calldata fees, uint256 amount) external {
        IMorpho(MORPHO).flashLoan(WETH, amount, abi.encode(tokens, fees, amount));
    }

    function onMorphoFlashLoan(uint256 amount, bytes calldata data) external {
        require(msg.sender == MORPHO, "Only Morpho");
        (address[] memory tokens, uint24[] memory fees, uint256 loanAmount) = abi.decode(data, (address[], uint24[], uint256));

        uint256 currentAmount = loanAmount;
        for (uint i = 0; i < tokens.length - 1; i++) {
            currentAmount = swap(tokens[i], tokens[i+1], fees[i], currentAmount);
        }

        // Repay Morpho
        IERC20(WETH).transfer(MORPHO, loanAmount);
        
        // Transfer profit
        uint256 balance = IERC20(WETH).balanceOf(address(this));
        if (balance > 0) IERC20(WETH).transfer(owner, balance);
    }

    function swap(address tokenIn, address tokenOut, uint24 fee, uint256 amountIn) internal returns (uint256) {
        IERC20(tokenIn).approve(UNI_V3, amountIn);
        return IUniswapV3Router(UNI_V3).exactInputSingle(IUniswapV3Router.ExactInputSingleParams({
            tokenIn: tokenIn,
            tokenOut: tokenOut,
            fee: fee,
            recipient: address(this),
            deadline: block.timestamp,
            amountIn: amountIn,
            amountOutMinimum: 0,
            sqrtPriceLimitX96: 0
        }));
    }

    receive() external payable {}
}
