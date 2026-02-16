
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

interface IERC20 {
    function totalSupply() external view returns (uint256);
    function balanceOf(address account) external view returns (uint256);
    function transfer(address recipient, uint256 amount) external returns (bool);
    function approve(address spender, uint256 amount) external returns (bool);
}

interface IUniswapV2Router {
    function swapExactTokensForTokens(uint amountIn, uint amountOutMin, address[] calldata path, address to, uint deadline) external returns (uint[] memory amounts);
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

contract MclawSpecial {
    address constant WETH = 0x4200000000000000000000000000000000000006;
    address constant MCLAWD = 0x98a98d2c0f7c1649E076082d828133B22d066C44;
    address constant UNI_V3 = 0x2626664c2603336E57B271c5C0b26F421741e481;
    address constant AERO_V2 = 0xcF77a3Ba9A5CA399B7C97c7a1C7f6F1a4f79D2f8;
    address constant MORPHO = 0xBBBBBbbBBb9cC5E90E3b3Af64bdAF62C37EEFFCb;

    address owner;

    constructor() {
        owner = msg.sender;
        IERC20(WETH).approve(UNI_V3, type(uint256).max);
        IERC20(MCLAWD).approve(UNI_V3, type(uint256).max);
        IERC20(WETH).approve(AERO_V2, type(uint256).max);
        IERC20(MCLAWD).approve(AERO_V2, type(uint256).max);
    }

    function execute(uint256 amount, uint8 mode) external {
        IMorpho(MORPHO).flashLoan(WETH, amount, abi.encode(mode, amount));
    }

    function onMorphoFlashLoan(uint256 amount, bytes calldata data) external {
        require(msg.sender == MORPHO, "Only Morpho");
        (uint8 mode, uint256 loanAmount) = abi.decode(data, (uint8, uint256));

        if (mode == 1) { // Buy Uni V3, Sell Aero V2
            uint256 mclawOut = buyUniV3(loanAmount);
            sellAeroV2(mclawOut);
        } else { // Buy Aero V2, Sell Uni V3
            uint256 mclawOut = buyAeroV2(loanAmount);
            sellUniV3(mclawOut);
        }

        IERC20(WETH).transfer(MORPHO, loanAmount);
        // Transfer profit
        uint256 profit = IERC20(WETH).balanceOf(address(this));
        if (profit > 0) IERC20(WETH).transfer(owner, profit);
    }

    function buyUniV3(uint256 amountIn) internal returns (uint256) {
        return IUniswapV3Router(UNI_V3).exactInputSingle(IUniswapV3Router.ExactInputSingleParams({
            tokenIn: WETH,
            tokenOut: MCLAWD,
            fee: 10000,
            recipient: address(this),
            deadline: block.timestamp,
            amountIn: amountIn,
            amountOutMinimum: 0,
            sqrtPriceLimitX96: 0
        }));
    }

    function sellUniV3(uint256 amountIn) internal returns (uint256) {
        return IUniswapV3Router(UNI_V3).exactInputSingle(IUniswapV3Router.ExactInputSingleParams({
            tokenIn: MCLAWD,
            tokenOut: WETH,
            fee: 10000,
            recipient: address(this),
            deadline: block.timestamp,
            amountIn: amountIn,
            amountOutMinimum: 0,
            sqrtPriceLimitX96: 0
        }));
    }

    function buyAeroV2(uint256 amountIn) internal returns (uint256) {
        address[] memory path = new address[](2);
        path[0] = WETH;
        path[1] = MCLAWD;
        IUniswapV2Router(AERO_V2).swapExactTokensForTokens(amountIn, 0, path, address(this), block.timestamp);
        return IERC20(MCLAWD).balanceOf(address(this));
    }

    function sellAeroV2(uint256 amountIn) internal returns (uint256) {
        address[] memory path = new address[](2);
        path[0] = MCLAWD;
        path[1] = WETH;
        IUniswapV2Router(AERO_V2).swapExactTokensForTokens(amountIn, 0, path, address(this), block.timestamp);
        return IERC20(WETH).balanceOf(address(this));
    }
}
