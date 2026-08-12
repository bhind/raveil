package chipyard.raveil

import chisel3._
import org.chipsalliance.cde.config.{Config, Parameters}
import freechips.rocketchip.diplomacy._
import freechips.rocketchip.rocket.DCacheTLNodeTransformKey
import freechips.rocketchip.tilelink._
import freechips.rocketchip.util._

/**
  * Adds a structural request marker at the DCache-local TileLink boundary.
  * The marker uses TileLink request metadata. A pinned, ephemeral TLXbar patch
  * preserves negotiated request fields and initializes absent client fields to
  * their declared false default; the owned manager latches it for A/D accounting.
  *
  * The bit proves only that a request crossed this structural adapter. It does
  * not identify an instruction, PC, ELF, or semantic initiator.
  */
class RaveilDCacheOriginTagger(implicit p: Parameters) extends LazyModule {
  val node = TLAdapterNode(clientFn = { cp =>
    cp.v1copy(requestFields =
      BundleField.union(cp.requestFields :+ RaveilDCacheOriginField()))
  })

  lazy val module = new LazyModuleImp(this) {
    (node.in zip node.out).foreach { case ((in, _), (out, _)) =>
      out.a.valid := in.a.valid
      in.a.ready := out.a.ready
      Connectable.waiveUnmatched(out.a.bits, in.a.bits) match {
        case (sink, source) => sink.squeezeAll :<= source.squeezeAll
      }
      out.a.bits.user(RaveilDCacheOrigin) := true.B

      out.c.valid := in.c.valid
      in.c.ready := out.c.ready
      Connectable.waiveUnmatched(out.c.bits, in.c.bits) match {
        case (sink, source) => sink.squeezeAll :<= source.squeezeAll
      }
      out.c.bits.user(RaveilDCacheOrigin) := true.B

      in.b.valid := out.b.valid
      out.b.ready := in.b.ready
      Connectable.waiveUnmatched(in.b.bits, out.b.bits) match {
        case (sink, source) => sink.squeezeAll :<= source.squeezeAll
      }

      in.d.valid := out.d.valid
      out.d.ready := in.d.ready
      Connectable.waiveUnmatched(in.d.bits, out.d.bits) match {
        case (sink, source) => sink.squeezeAll :<= source.squeezeAll
      }

      out.e.valid := in.e.valid
      in.e.ready := out.e.ready
      Connectable.waiveUnmatched(out.e.bits, in.e.bits) match {
        case (sink, source) => sink.squeezeAll :<= source.squeezeAll
      }
    }
  }
}

class WithRaveilDCacheOriginTagger extends Config((site, here, up) => {
  case DCacheTLNodeTransformKey => (p: Parameters) => (upstream: TLNode) => {
    implicit val implicitParameters: Parameters = p
    val tagger = LazyModule(new RaveilDCacheOriginTagger()(p))
    tagger.node := upstream
    tagger.node
  }
})

class RaveilOwnedRocketConfig extends Config(
  new WithRaveilOwnedBuildSystem ++
  new WithRaveilOwnedMemorySourceRange(8224, 8256) ++
  new WithRaveilDCacheOriginTagger ++
  new testchipip.soc.WithNoScratchpads ++
  new chipyard.RocketConfig
)

class RaveilOwnedSmallBoomConfig extends Config(
  new WithRaveilOwnedBuildSystem ++
  new WithRaveilOwnedMemorySourceRange(8288, 8320) ++
  new WithRaveilDCacheOriginTagger ++
  new testchipip.soc.WithNoScratchpads ++
  new chipyard.SmallBoomConfig
)
