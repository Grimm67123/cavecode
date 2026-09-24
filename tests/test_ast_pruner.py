"""
Tests for Tree-Sitter AST-Aware Pruning Engine in CaveCode.
"""

from cavecode.ast_pruner import ASTPruner


def test_c_ast_signature_and_assert_pruning():
    code = """CURLcode
Curl_http_setup_conn(struct Curl_easy *data,
                     struct connectdata *conn)
{
    DEBUGASSERT(data != NULL);
    if(data == NULL) {
        return CURLE_FAILED_INIT;
    }
    return CURLE_OK;
}"""
    pruned = ASTPruner.prune_ast(code, "c")
    assert "CURLcode Curl_http_setup_conn(struct Curl_easy *data, struct connectdata *conn) {" in pruned
    assert "DEBUGASSERT" not in pruned
    assert "return CURLE_OK;" in pruned


def test_go_ast_signature_and_klog_pruning():
    code = """func (d *DaemonSetsController) syncNodes(
\tctx context.Context,
\tdsKey string,
) error {
\tlogger.V(4).Info("Syncing nodes")
\tif err != nil {
\t\treturn err
\t}
\treturn nil
}"""
    pruned = ASTPruner.prune_ast(code, "go")
    assert "func (d *DaemonSetsController) syncNodes(ctx context.Context, dsKey string) error {" in pruned
    assert 'logger.V(4)' not in pruned
    assert "return nil" in pruned


def test_javascript_ast_argument_inlining():
    code = """function dispatch(
  action,
  payload
) {
  settle(
    resolve,
    reject,
    response
  );
  return true;
}"""
    pruned = ASTPruner.prune_ast(code, "javascript")
    assert "function dispatch(action, payload) {" in pruned
    assert "settle(resolve, reject, response)" in pruned


def test_rust_ast_signature_inlining():
    code = """fn compute_hash(
    data: &[u8],
    seed: u64,
) -> u64 {
    debug!("computing hash");
    42
}"""
    pruned = ASTPruner.prune_ast(code, "rust")
    assert "fn compute_hash(data: &[u8], seed: u64) -> u64 {" in pruned
    assert "debug!" not in pruned
    assert "42" in pruned
