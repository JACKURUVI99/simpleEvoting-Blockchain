// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

contract Voting {

    string[] public candidates;
    mapping(uint => uint) public count;
    mapping(address => bool) public voted;
    address public owner;
    bool public active;

    constructor(string[] memory names) {
        owner = msg.sender;
        active = true;
        for (uint i = 0; i < names.length; i++) {
            candidates.push(names[i]);
        }
    }

    function vote(uint id) public {
        require(active == true, "Election is stopped");
        require(voted[msg.sender] == false, "You already voted");
        require(id < candidates.length, "Wrong candidate number");
        voted[msg.sender] = true;
        count[id] = count[id] + 1;
    }

    function stopElection() public {
        require(msg.sender == owner, "Only owner can stop election");
        active = false;
    }

    function getTotalCandidates() public view returns (uint) {
        return candidates.length;
    }

    function getVoteCount(uint id) public view returns (uint) {
        return count[id];
    }
}
