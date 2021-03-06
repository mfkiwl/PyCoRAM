parameter mem_offset = 0;
parameter address_width = 17;
parameter dma_size = 256;
parameter data_size = 16 * 1024;

reg [31:0] read_val;

initial begin
  #1000;
  wait(sim_resetn == 1);
  nclk();
  $display("write mem_offset");
  iochannel_write_cthread_random_write_coramiochannel_0(mem_offset, 0);
  
  nclk();
  $display("write address_width");
  iochannel_write_cthread_random_write_coramiochannel_0(address_width, 0);
  
  nclk();
  $display("write dma_size");
  iochannel_write_cthread_random_write_coramiochannel_0(dma_size, 0);
  
  nclk();
  $display("write data_size");
  iochannel_write_cthread_random_write_coramiochannel_0(data_size, 0);
  
  nclk();
  iochannel_read_cthread_random_write_coramiochannel_0(read_val, 0);
  nclk();
  $display("iochannel cyclecount=%d", read_val);
  #1000;
  $finish;
end
