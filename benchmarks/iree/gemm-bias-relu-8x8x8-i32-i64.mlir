// Raveil-authored canonical T-0186 import fixture: GEMM plus column bias and signed ReLU.
module {
  func.func @main(%lhs: tensor<8x8xi32>, %rhs: tensor<8x8xi32>, %bias: tensor<8xi64>) -> tensor<8x8xi64> {
    %zero = arith.constant 0 : i64
    %empty = tensor.empty() : tensor<8x8xi64>
    %init = linalg.fill ins(%zero : i64) outs(%empty : tensor<8x8xi64>) -> tensor<8x8xi64>
    %result = linalg.generic {
      indexing_maps = [
        affine_map<(m, n, k) -> (m, k)>,
        affine_map<(m, n, k) -> (k, n)>,
        affine_map<(m, n, k) -> (m, n)>
      ],
      iterator_types = ["parallel", "parallel", "reduction"]
    } ins(%lhs, %rhs : tensor<8x8xi32>, tensor<8x8xi32>)
      outs(%init : tensor<8x8xi64>) {
      ^bb0(%left: i32, %right: i32, %acc: i64):
        %left64 = arith.extsi %left : i32 to i64
        %right64 = arith.extsi %right : i32 to i64
        %product = arith.muli %left64, %right64 : i64
        %sum = arith.addi %acc, %product : i64
        linalg.yield %sum : i64
    } -> tensor<8x8xi64>
    %output = linalg.generic {
      indexing_maps = [
        affine_map<(m, n) -> (m, n)>,
        affine_map<(m, n) -> (n)>,
        affine_map<(m, n) -> (m, n)>
      ],
      iterator_types = ["parallel", "parallel"]
    } ins(%result, %bias : tensor<8x8xi64>, tensor<8xi64>)
      outs(%empty : tensor<8x8xi64>) {
      ^bb0(%value: i64, %column_bias: i64, %unused: i64):
        %biased = arith.addi %value, %column_bias : i64
        %activated = arith.maxsi %biased, %zero : i64
        linalg.yield %activated : i64
    } -> tensor<8x8xi64>
    return %output : tensor<8x8xi64>
  }
}
