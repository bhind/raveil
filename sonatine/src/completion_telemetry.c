#include "completion_telemetry.h"
#include "console.h"

static void write_cookie(const uint8_t cookie[16]) {
  static const char digits[]="0123456789abcdef";
  for(size_t index=0;index<16u;++index) {
    console_putc(digits[cookie[index]>>4u]);
    console_putc(digits[cookie[index]&0x0fu]);
  }
}

void completion_telemetry_emit(
    const struct raveil_completion_record_v1 *completion,
    uint64_t smoke_path_ticks) {
  console_write("RAVEIL-COMPLETION-V1 job=");
  console_write_dec(completion->job_id);
  console_write(" epoch="); console_write_dec(completion->execution_epoch);
  console_write(" sequence="); console_write_dec(completion->execution_sequence);
  console_write(" cookie="); write_cookie(completion->completion_cookie);
  console_write(" status="); console_write_dec(completion->status);
  console_write(" detail="); console_write_dec(completion->detail);
  console_write(" smoke_path_ticks="); console_write_dec(smoke_path_ticks);
  console_write(" outputs=");
  if(completion->output_count==0u) {
    console_putc('-');
  } else {
    for(uint16_t index=0;index<completion->output_count;++index) {
      if(index!=0u) console_putc(',');
      console_write_dec(completion->outputs[index].object_id); console_putc(':');
      console_write_dec(completion->outputs[index].generation); console_putc(':');
      console_write_dec(completion->outputs[index].version);
    }
  }
  console_write("\n");
}
