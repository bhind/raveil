#include "VAffineFoldRegion.h"
#include "verilated.h"
#include <array>
#include <cstdint>
#include <fstream>
#include <iostream>
#include <stdexcept>
#include <string>
#include <vector>
#include "fold_vectors.h"
#include "fold_config.h"

static void require(bool v, const std::string& message) {
  if (!v) throw std::runtime_error(message);
}

int main(int argc, char** argv) {
  Verilated::commandArgs(argc, argv);
  if (argc != 2) return 2;
  std::ofstream trace(argv[1]);
  if (!trace) return 2;
  VAffineFoldRegion top;
  top.clock=0; top.reset=1; top.io_start=0; top.io_cancel=0;
  top.io_req_ready=0; top.io_resp_valid=0; top.io_resp_bits_data=0;
  top.io_resp_bits_error=0;
  configure(top, std::vector<uint32_t>(65,0));
  for (int n=0;n<3;++n) { top.clock=0;top.eval();top.clock=1;top.eval(); }
  top.reset=0;
  unsigned passed=0;
  try {
    for (unsigned seed : {1u, 73u, 991u}) for (const auto& c: cases) {
      std::array<uint32_t,1024> memory;
      memory.fill(0xdeadbeefu);
      for (size_t n=0;n<c.a.size();++n) memory[n]=c.a[n];
      for (size_t n=0;n<c.b.size();++n) memory[324+n]=c.b[n];
      auto original=memory;
      configure(top,c.cfg);
      top.io_start=1;top.io_cancel=0;top.io_req_ready=0;top.io_resp_valid=0;
      top.clock=0;top.eval();top.clock=1;top.eval();
      top.io_start=0;
      bool pending=false, pendingWrite=false, injected=false, responseError=false;
      bool held=false;
      unsigned delay=0, accepted=0, completed=0, cycles=0, reads=0, writes=0;
      uint32_t responseData=0, heldAddress=0,heldData=0,heldWrite=0;
      uint32_t rng=seed;
      // Testbench-specific bound, not a hardware latency guarantee.
      const uint64_t watchdog=1000+uint64_t(c.expected.size())*64*16*32;
      for (;cycles<watchdog;++cycles) {
        rng=rng*1664525u+1013904223u;
        top.clock=0;
        top.io_cancel=0;
        top.io_start=0;
        top.io_req_ready=(!pending && ((rng>>8)%4!=0));
        top.io_resp_valid=pending && delay==0;
        top.io_resp_bits_data=responseData;
        top.io_resp_bits_error=responseError;
        top.eval();
        // Cancel a held request: force one stall before sampling cancellation.
        if (!injected && ((c.mode==2 && top.io_req_valid && !top.io_req_bits_write) ||
                          (c.mode==4 && top.io_req_valid && top.io_req_bits_write))) {
          top.io_req_ready=0;top.io_cancel=1;injected=true;
        } else if (!injected &&
                   ((c.mode==1 && cycles==0) ||
                    (c.mode==3 && pending && !pendingWrite) ||
                    (c.mode==5 && pending && pendingWrite) ||
                    (c.mode==9 && pending && pendingWrite && delay==0) ||
                    (c.mode==11 && completed==2 && !pending && !top.io_req_valid) ||
                    (c.mode==12 && cycles==3) ||
                    (c.mode==13 && pending && delay==0))) {
          top.io_cancel=1;injected=true;
        }
        if (c.mode==8 && cycles==1) {
          auto corrupt=c.cfg;corrupt[0]=0;corrupt[1]=0;corrupt[49]=0;
          configure(top,corrupt);top.io_start=1;injected=true;
        }
        top.eval();
        if (held) {
          require(top.io_req_valid && top.io_req_bits_address==heldAddress &&
                  top.io_req_bits_data==heldData && top.io_req_bits_write==heldWrite,
                  "request changed under backpressure");
        }
        held=top.io_req_valid && !top.io_req_ready;
        heldAddress=top.io_req_bits_address;heldData=top.io_req_bits_data;
        heldWrite=top.io_req_bits_write;
        const bool takeReq=top.io_req_valid && top.io_req_ready;
        const bool takeResp=top.io_resp_valid && top.io_resp_ready;
        const auto address=top.io_req_bits_address;
        const auto data=top.io_req_bits_data;
        const bool write=top.io_req_bits_write;
        if (takeReq) {
          require(!pending && address<1024,"multiple outstanding or invalid address");
          require(write ? (address>=648 && address<648+c.expected.size()) :
                    (address<c.a.size() || (address>=324 && address<324+c.b.size())),
                  "transaction outside declared region");
          pending=true;pendingWrite=write;delay=1+((rng>>16)%7);
          responseError=(!injected && ((c.mode==6 && !write)||(c.mode==7 && write) ||
                                      (c.mode==13 && !write)));
          if(responseError && c.mode!=13) injected=true;
          if(write) { ++writes;if(!responseError) memory[address]=data; }
          else ++reads;
          responseData=write ? 0 : memory[address];
          ++accepted;
          trace<<seed<<" "<<c.name<<" req "<<cycles<<" "<<write<<" "<<address<<" "<<data<<"\n";
        }
        if(takeResp) {
          require(pending,"orphan response");
          pending=false;++completed;
          trace<<seed<<" "<<c.name<<" resp "<<cycles<<" "<<responseData<<" "<<responseError<<"\n";
        }
        top.clock=1;top.eval();
        if(pending && delay && !takeReq) --delay;
        if(top.io_done) break;
      }
      require(cycles<watchdog,"timeout");
      require(!top.io_busy && !pending && !held && accepted==completed,"undrained completion");
      for(size_t n=0;n<648;++n) require(memory[n]==original[n],"input modified");
      for(size_t n=648+c.expected.size();n<1024;++n)
        require(memory[n]==original[n],"unowned output modified");
      const bool ok=c.mode==0 || c.mode==8;
      require(bool(top.io_success)==ok,"wrong publication state");
      require(bool(top.io_fault)==(c.mode==6 || c.mode==7 || c.mode==10 || c.mode==13),"wrong fault state");
      require(bool(top.io_cancelled)==((c.mode>=1 && c.mode<=5) || c.mode==9 || c.mode>=11),"wrong cancel state");
      if(c.mode!=0 && c.mode!=10) require(injected,"protocol scenario not reached");
      if(c.mode==10 || c.mode==1) require(accepted==0,"effect before admission/cancel");
      if(ok) {
        for(size_t n=0;n<c.expected.size();++n)
          require(memory[648+n]==c.expected[n],"oracle mismatch at "+std::to_string(n));
        unsigned loads=0;
        for(unsigned n=0;n<c.cfg[8];++n) loads+=(c.cfg[49+n]>>28)==1;
        require(writes==c.expected.size() && reads==c.expected.size()*c.cfg[3]*loads,
                "wrong transaction counts");
      }
      std::cout<<"PASS "<<seed<<" "<<c.name<<" cells="<<(ok?c.expected.size():0)
               <<" accepted="<<accepted<<" completed="<<completed<<"\n";
      ++passed;
    }
    std::cout<<"PASS total="<<passed<<" evidence=RTL-functional-simulation\n";
  } catch(const std::exception& e) {
    std::cerr<<"FAIL after "<<passed<<" cases: "<<e.what()<<"\n";return 1;
  }
  return 0;
}
