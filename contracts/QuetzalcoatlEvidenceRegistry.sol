// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

/**
 * @title QuetzalcoatlEvidenceRegistry
 * @dev Cryptographic evidence anchoring registry for Quantum Digital Signatures (QDS).
 * Anchors Merkle roots and high-severity threat incidents to an immutable blockchain ledger,
 * providing non-repudiable audit proofs and independent mathematical verification.
 */
contract QuetzalcoatlEvidenceRegistry {
    address public owner;

    struct MerkleRootEntry {
        bytes32 root;
        uint256 timestamp;
        uint256 blockNumber;
        uint256 recordCount;
        string metadataURI; // IPFS or off-chain storage URI
    }

    struct IncidentRecord {
        bytes32 incidentLeafHash;
        uint256 sessionIndex;
        string threatType;
        uint256 timestamp;
        address reporter;
    }

    // Mapping from Merkle root to its registration record
    mapping(bytes32 => MerkleRootEntry) public anchoredRoots;
    bytes32[] public rootHistory;

    // Mapping from incident leaf hash to its record
    mapping(bytes32 => IncidentRecord) public incidents;
    bytes32[] public incidentHistory;

    // Events for real-time monitoring by Security Operations Center (SOC)
    event MerkleRootAnchored(
        bytes32 indexed root,
        uint256 indexed blockNumber,
        uint256 recordCount,
        uint256 timestamp,
        string metadataURI
    );

    event IncidentAnchored(
        bytes32 indexed leafHash,
        uint256 indexed sessionIndex,
        string threatType,
        uint256 timestamp,
        address indexed reporter
    );

    event TamperAlertTriggered(
        bytes32 indexed expectedRoot,
        bytes32 indexed computedRoot,
        string reason,
        uint256 timestamp
    );

    modifier onlyOwner() {
        require(msg.sender == owner, "Quetzalcoatl: caller is not owner");
        _;
    }

    constructor() {
        owner = msg.sender;
    }

    /**
     * @notice Anchors a Merkle root calculated from a batch of QDS verification events.
     * @param root The 32-byte Merkle tree root hash.
     * @param recordCount Number of quantum verification sessions in this tree.
     * @param metadataURI Off-chain URI detailing the session batch (e.g. IPFS hash).
     */
    function recordMerkleRoot(
        bytes32 root,
        uint256 recordCount,
        string calldata metadataURI
    ) external onlyOwner {
        require(root != bytes32(0), "Invalid root hash");
        require(anchoredRoots[root].timestamp == 0, "Root already anchored");

        anchoredRoots[root] = MerkleRootEntry({
            root: root,
            timestamp: block.timestamp,
            blockNumber: block.number,
            recordCount: recordCount,
            metadataURI: metadataURI
        });

        rootHistory.push(root);

        emit MerkleRootAnchored(root, block.number, recordCount, block.timestamp, metadataURI);
    }

    /**
     * @notice Anchors an individual critical security incident (e.g., detected quantum forgery).
     * @param leafHash The SHA-256 / Keccak-256 hash of the canonical incident log.
     * @param sessionIndex The local ledger index of the session.
     * @param threatType Threat classification (e.g., "FORGERY", "CHANNEL_MANIPULATION").
     */
    function recordIncidentLeaf(
        bytes32 leafHash,
        uint256 sessionIndex,
        string calldata threatType
    ) external onlyOwner {
        require(leafHash != bytes32(0), "Invalid leaf hash");

        incidents[leafHash] = IncidentRecord({
            incidentLeafHash: leafHash,
            sessionIndex: sessionIndex,
            threatType: threatType,
            timestamp: block.timestamp,
            reporter: msg.sender
        });

        incidentHistory.push(leafHash);

        emit IncidentAnchored(leafHash, sessionIndex, threatType, block.timestamp, msg.sender);
    }

    /**
     * @notice Pure cryptographic verification of a Merkle inclusion proof using SHA-256.
     * @param leaf The leaf hash of the QDS event being verified.
     * @param proof Array of sibling hashes along the Merkle branch.
     * @param isRight Array of booleans indicating if the sibling is on the right.
     * @param expectedRoot The anchored root to verify against.
     * @return isValid True if the mathematical path hashes to expectedRoot.
     */
    function verifyInclusionProofSHA256(
        bytes32 leaf,
        bytes32[] calldata proof,
        bool[] calldata isRight,
        bytes32 expectedRoot
    ) external pure returns (bool isValid) {
        require(proof.length == isRight.length, "Mismatched proof path dimensions");

        bytes32 current = leaf;

        for (uint256 i = 0; i < proof.length; i++) {
            if (isRight[i]) {
                // current is left, sibling is right
                current = sha256(abi.encodePacked(current, proof[i]));
            } else {
                // sibling is left, current is right
                current = sha256(abi.encodePacked(proof[i], current));
            }
        }

        return current == expectedRoot;
    }

    /**
     * @notice Returns total number of anchored Merkle roots.
     */
    function getRootCount() external view returns (uint256) {
        return rootHistory.length;
    }

    /**
     * @notice Returns total number of registered incidents.
     */
    function getIncidentCount() external view returns (uint256) {
        return incidentHistory.length;
    }
}

