#include "VAffineFoldRegion.h"
#include "verilated.h"
#include <array>
#include <cstdint>
#include <fstream>
#include <iostream>
#include <stdexcept>
#include <string>
#include <vector>
#include "fold_config.h"
static void require(bool v,const std::string& s) { if(!v) throw std::runtime_error(s); }
static void word(std::ostream& out,uint32_t n) {
  for(unsigned i=0;i<4;++i) out.put(char((n>>(8*i))&255));
}
static uint32_t readword(std::istream& in) {
  uint32_t v=0;for(unsigned i=0;i<4;++i) {
    int b=in.get();require(b!=EOF,"truncated request");v|=uint32_t(b)<<(8*i);
  }return v;
}
static void event(std::ostream& out,uint32_t kind,uint32_t cycle,uint32_t write,
                  uint32_t address,uint32_t data,uint32_t error) {
  for(auto n:{kind,cycle,write,address,data,error}) word(out,n);
}
struct Request { std::vector<uint32_t> cfg,a,b; uint32_t seed,cancelAfter,faultAt; };
int main(int argc,char** argv) {
  if(argc!=3) return 2;
  Request request;
  try {
    std::ifstream input(argv[1],std::ios::binary);require(bool(input),"missing request");
    require(readword(input)==0x4d465231 && readword(input)==1,"unsupported transport");
    auto la=readword(input),lb=readword(input);require(la<=324 && lb<=324,"input length");
    request.seed=readword(input);request.cancelAfter=readword(input);request.faultAt=readword(input);
    require(readword(input)==0,"reserved transport word");
    for(unsigned i=0;i<65;++i) request.cfg.push_back(readword(input));
    for(unsigned i=0;i<la;++i) request.a.push_back(readword(input));
    for(unsigned i=0;i<lb;++i) request.b.push_back(readword(input));
    require(input.get()==EOF,"trailing request data");
    require(request.cfg[1]>=1 && request.cfg[1]<=16 && request.cfg[2]>=1 && request.cfg[2]<=16,
            "transport output bounds");
    require(request.cfg[5]==la && request.cfg[6]==lb,"transport lengths differ");
  }catch(const std::exception& e) { std::cerr<<e.what()<<"\n";return 2; }
  std::ofstream trace(std::string(argv[2])+"/trace.bin",std::ios::binary);
  if(!trace) return 2;
  VAffineFoldRegion top;
  top.clock=0; top.reset=1; top.io_start=0; top.io_cancel=0;
  top.io_req_ready=0; top.io_resp_valid=0; top.io_resp_bits_data=0;
  top.io_resp_bits_error=0;
  configure(top, std::vector<uint32_t>(65,0));
  for (int n=0;n<3;++n) { top.clock=0;top.eval();top.clock=1;top.eval(); }
  top.reset=0;
  unsigned passed=0;
  try {
    {
      const unsigned seed=request.seed;
      const auto& c=request;
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
      uint32_t pendingAddress=0, responseData=0, heldAddress=0,heldData=0,heldWrite=0;
      uint32_t rng=seed;
      // Testbench-specific bound, not a hardware latency guarantee.
      const uint64_t watchdog=1000+uint64_t(size_t(c.cfg[1])*c.cfg[2])*64*16*32;
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
        top.io_cancel=request.cancelAfter && completed>=request.cancelAfter;
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
          require(write ? (address>=648 && address<648+size_t(c.cfg[1])*c.cfg[2]) :
                    (address<c.a.size() || (address>=324 && address<324+c.b.size())),
                  "transaction outside declared region");
          pending=true;pendingWrite=write;pendingAddress=address;delay=1+((rng>>16)%7);
          responseError=request.faultAt && accepted+1==request.faultAt;
          if(write) { ++writes;if(!responseError) memory[address]=data; }
          else ++reads;
          responseData=write ? 0 : memory[address];
          ++accepted;
          event(trace,0,cycles,write,address,data,0);
        }
        if(takeResp) {
          require(pending,"orphan response");
          pending=false;++completed;
          event(trace,1,cycles,pendingWrite,pendingAddress,responseData,responseError);
        }
        top.clock=1;top.eval();
        if(pending && delay && !takeReq) --delay;
        if(top.io_done) break;
      }
      require(cycles<watchdog,"timeout");
      require(!top.io_busy && !pending && !held && accepted==completed,"undrained completion");
      for(size_t n=0;n<648;++n) require(memory[n]==original[n],"input modified");
      for(size_t n=648+size_t(c.cfg[1])*c.cfg[2];n<1024;++n)
        require(memory[n]==original[n],"unowned output modified");
      const bool ok=top.io_success;
      trace.close();require(bool(trace),"trace write failed");
      if(ok) {
        std::ofstream output(std::string(argv[2])+"/output.bin",std::ios::binary);
        for(unsigned n=0;n<c.cfg[1]*c.cfg[2];++n) word(output,memory[648+n]);
        output.close();require(bool(output),"output write failed");
      }
      std::ofstream receipt(std::string(argv[2])+"/device.json");
      receipt<<"{\"schema\":\"raveil.fold-device/v1\",\"success\":"<<unsigned(top.io_success)
             <<",\"fault\":"<<unsigned(top.io_fault)<<",\"cancelled\":"<<unsigned(top.io_cancelled)
             <<",\"accepted\":"<<accepted<<",\"completed\":"<<completed
             <<",\"writes\":"<<writes<<",\"reads\":"<<reads<<"}\n";
      receipt.close();require(bool(receipt),"receipt write failed");
      return ok ? 0 : top.io_cancelled ? 130 : 2;
    }
  } catch(const std::exception& e) {
    std::cerr<<"FAIL: "<<e.what()<<"\n";return 1;
  }
}
