// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

// Multi-election factory. Anyone can create an election "room" with a password,
// add candidates, and is recorded as that room's creator. Voters join with the
// room id + password. NOTE: a blockchain has no secrets — the password is stored
// as a keccak256 hash and is a casual gate only, NOT cryptographically private.
contract Voting {

    struct Election {
        address creator;
        string title;
        bytes32 pwHash;
        bool active;
        bool exists;
        string[] candidates;
        mapping(uint => uint) count;
        mapping(address => bool) voted;
    }

    uint public electionCount;
    mapping(uint => Election) private elections;

    event ElectionCreated(uint indexed id, address indexed creator, string title);

    modifier onlyCreator(uint id) {
        require(elections[id].exists, "No such election");
        require(msg.sender == elections[id].creator, "Only the creator");
        _;
    }

    function createElection(string memory title, string memory password) public returns (uint) {
        electionCount++;
        uint id = electionCount;
        Election storage e = elections[id];
        e.creator = msg.sender;
        e.title = title;
        e.pwHash = keccak256(bytes(password));
        e.active = true;
        e.exists = true;
        emit ElectionCreated(id, msg.sender, title);
        return id;
    }

    function addCandidate(uint id, string memory name) public onlyCreator(id) {
        require(elections[id].active, "Election stopped");
        elections[id].candidates.push(name);
    }

    function vote(uint id, uint cand, string memory password) public {
        Election storage e = elections[id];
        require(e.exists, "No such election");
        require(e.active, "Election stopped");
        require(e.pwHash == keccak256(bytes(password)), "Wrong room password");
        require(!e.voted[msg.sender], "You already voted in this room");
        require(cand < e.candidates.length, "Bad candidate");
        e.voted[msg.sender] = true;
        e.count[cand]++;
    }

    function stopElection(uint id) public onlyCreator(id) {
        elections[id].active = false;
    }

    // --- views ---
    function getInfo(uint id) public view returns (string memory title, address creator, bool active, uint candidateCount) {
        Election storage e = elections[id];
        require(e.exists, "No such election");
        return (e.title, e.creator, e.active, e.candidates.length);
    }

    function getCandidate(uint id, uint i) public view returns (string memory name, uint votes) {
        Election storage e = elections[id];
        require(e.exists, "No such election");
        return (e.candidates[i], e.count[i]);
    }

    function hasVoted(uint id, address who) public view returns (bool) {
        return elections[id].voted[who];
    }
}
