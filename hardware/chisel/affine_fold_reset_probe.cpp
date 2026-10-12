// Functional probe of the documented coordinated core/responder reset.
// A separate test executable, never used as the workspace runtime.
#include "VAffineFoldRegion.h"
#include "verilated.h"
#include <array>
#include <vector>
#include <iostream>
#include <stdexcept>
#include "fold_config.h"
static void check(bool v,const char* s) { if(!v) throw std::runtime_error(s); }

struct System {
  VAffineFoldRegion top;
  std::array<uint32_t,1024> memory{};
  bool pending=false,write=false;
  uint32_t address=0,data=0;
  unsigned delay=0,reads=0,writes=0,completedWrites=0;
  void edge() { top.clock=1;top.eval();top.clock=0;top.eval(); }
  void reset() {
    // Reset the responder at the same boundary: no stale reply may survive.
    pending=false;delay=0;reads=writes=completedWrites=0;
    top.io_start=0;top.io_cancel=0;top.io_req_ready=0;
    top.io_resp_valid=0;top.io_resp_bits_data=0;top.io_resp_bits_error=0;
    top.reset=1;top.clock=0;top.eval();edge();edge();
    top.reset=0;top.eval();
    check(!top.io_busy && !top.io_done && !top.io_success &&
          !top.io_fault && !top.io_cancelled,"reset did not clear result/control");
  }
  void start(bool multiply) {
    std::vector<uint32_t> c(65,0);
    c[0]=0x4d463031;c[1]=1;c[2]=2;c[3]=1;c[5]=2;c[6]=2;c[7]=2;c[8]=4;
    c[12]=1;c[14]=1;c[17]=1;
    c[49]=0x10000000;c[50]=0x12400000;
    c[51]=multiply?0x50080000:0x20080000;c[52]=0x30000000;
    configure(top,c);top.io_start=1;top.eval();edge();top.io_start=0;top.eval();
  }
  void prepare(bool stall) {
    top.io_req_ready=!pending && !stall;
    top.io_resp_valid=pending && delay==0;
    top.io_resp_bits_data=data;top.io_resp_bits_error=0;top.eval();
  }
  void tick() {
    bool request=top.io_req_valid && top.io_req_ready;
    bool response=top.io_resp_valid && top.io_resp_ready;
    if(request) {
      check(!pending,"two outstanding requests");
      write=top.io_req_bits_write;address=top.io_req_bits_address;
      check(write?(address==648||address==649):
                  (address==0||address==1||address==324||address==325),"bad address");
      if(write) { memory[address]=top.io_req_bits_data;++writes; }
      else ++reads;
      data=write?0:memory[address];pending=true;delay=4;
    }
    if(response) {check(pending,"orphan reply");pending=false;if(write)++completedWrites;}
    edge();if(pending && delay && !request)--delay;
  }
};

int main() {
  try {
    for(unsigned phase=0;phase<6;++phase) {
      System s;s.reset();
      s.memory[0]=1;s.memory[1]=2;s.memory[324]=4;s.memory[325]=5;
      s.start(false);
      bool reached=false;
      for(unsigned cycle=0;cycle<1000;++cycle) {
        const bool stall=(phase==1||phase==3);
        // Stall only the selected request kind.
        s.prepare(false);
        s.prepare(stall && s.top.io_req_valid &&
                  (bool(s.top.io_req_bits_write)==(phase==3)));
        bool trigger=(phase==0 && cycle==2) ||
          (phase==1 && s.top.io_req_valid && !s.top.io_req_bits_write && !s.top.io_req_ready) ||
          (phase==2 && s.pending && !s.write && s.delay>0) ||
          (phase==3 && s.top.io_req_valid && s.top.io_req_bits_write && !s.top.io_req_ready) ||
          (phase==4 && s.pending && s.write && s.delay>0) ||
          (phase==5 && s.completedWrites==1 && !s.pending);
        if(trigger) {
          check(s.top.io_busy && !s.top.io_success,"reset scenario already complete");
          if(phase==4 || phase==5)check(s.memory[648]==5,"private write scenario not reached");
          s.reset();reached=true;break;
        }
        s.tick();
      }
      check(reached,"reset phase not reached");
      // Preserve private partial outputs, replace inputs and configure a
      // different program. Successful retry must overwrite both output words.
      s.memory[0]=3;s.memory[1]=7;s.memory[324]=11;s.memory[325]=13;
      s.start(true);
      unsigned cycles=0;
      for(;cycles<1000 && !s.top.io_done;++cycles) {s.prepare(false);s.tick();}
      check(cycles<1000 && s.top.io_success && !s.top.io_fault &&
            !s.top.io_cancelled && !s.top.io_busy && !s.pending,"retry failed");
      check(s.reads==4 && s.writes==2 && s.completedWrites==2,"retry traffic differs");
      check(s.memory[648]==33 && s.memory[649]==91,"stale result or wrong retry values");
      std::cout<<"PASS reset_phase="<<phase<<" retry_output=33,91 reads=4 writes=2\n";
    }
    std::cout<<"PASS coordinated_reset=6 evidence=RTL-functional-simulation\n";
    return 0;
  }catch(const std::exception& e){std::cerr<<"FAIL "<<e.what()<<"\n";return 1;}
}
