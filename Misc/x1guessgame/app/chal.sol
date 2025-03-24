pragma solidity ^0.8.28;

contract Challenge {
    bytes32 public target;
    bool public isClaimed;
    address public winner;

    modifier isNotContract(address _addr) {
        uint256 size;
        assembly {
            size := extcodesize(_addr)
        }
        require(size == 0, "caller is a contract");
        _;
    }

    constructor(bytes32 _target) payable {
        target = _target;
    }

    function claim(bytes memory answer) public isNotContract(msg.sender) {
        require(!isClaimed, "already claimed");
        require(keccak256(answer) == target, "bad answer");
        isClaimed = true;
        winner = msg.sender;
        (bool success, ) = payable(msg.sender).call{
            value: address(this).balance
        }("");
        require(success, "failed to send");
    }
}
