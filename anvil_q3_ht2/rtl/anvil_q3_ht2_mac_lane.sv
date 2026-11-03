module anvil_q3_ht2_mac_lane (
  input wire clk,rst_n,flush,enable,
  input wire product_in_valid,
  input wire [31:0] weight_f32,activation_f32,
  input wire [2:0] product_stripe,
  input wire reduction_valid,
  input wire [1:0] reduction_level,reduction_index,
  output wire arithmetic_error,final_valid,
  output wire [31:0] final_sum
);
  reg [31:0] stripes [0:7];
  reg [31:0] level_one [0:3];
  reg [31:0] level_two [0:1];
  reg [4:0] tag [0:4];
  wire product_valid,product_error;
  wire [31:0] product;
  wire adder_valid=product_valid || reduction_valid;
  reg [31:0] add_a,add_b;
  reg [4:0] incoming_tag;
  wire add_out_valid,add_out_error;
  wire [31:0] add_out_result;
  wire retire_valid,retire_error;
  wire [31:0] retire_result;
  integer i;

  anvil_q3_ht2_fp32_mul product_pipeline (
    .clk(clk),.rst_n(rst_n),.flush(flush),.enable(enable),
    .in_valid(product_in_valid),.in_a(weight_f32),.in_b(activation_f32),
    .out_valid(product_valid),.out_error(product_error),.out_result(product)
  );
  always @* begin
    add_a=0;
    add_b=0;
    incoming_tag=0;
    if (reduction_valid) begin
      incoming_tag={reduction_level,1'b0,reduction_index};
      case (reduction_level)
        1: begin
          add_a=stripes[{reduction_index,1'b0}];
          add_b=stripes[{reduction_index,1'b1}];
        end
        2: begin
          add_a=level_one[{reduction_index[0],1'b0}];
          add_b=level_one[{reduction_index[0],1'b1}];
        end
        3: begin
          add_a=level_two[0];
          add_b=level_two[1];
        end
        default: begin add_a=0; add_b=0; end
      endcase
    end else if (product_valid) begin
      add_a=stripes[product_stripe];
      add_b=product;
      incoming_tag={2'd0,product_stripe};
    end
  end

  anvil_q3_ht2_fp32_add stripe_and_tree_adder (
    .clk(clk),.rst_n(rst_n),.flush(flush),.enable(enable),
    .in_valid(adder_valid),.in_a(add_a),.in_b(add_b),
    .out_valid(add_out_valid),.out_error(add_out_error),
    .out_result(add_out_result),
    .retire_valid(retire_valid),.retire_error(retire_error),
    .retire_result(retire_result)
  );
  assign arithmetic_error=rst_n && !flush &&
    ((product_valid && product_error) || (retire_valid && retire_error));
  assign final_valid=retire_valid && !retire_error && tag[4][4:3]==3;
  assign final_sum=final_valid ? retire_result : 0;

  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      for (i=0;i<8;i=i+1) stripes[i]<=0;
      for (i=0;i<4;i=i+1) level_one[i]<=0;
      for (i=0;i<2;i=i+1) level_two[i]<=0;
      for (i=0;i<5;i=i+1) tag[i]<=0;
    end else if (flush) begin
      for (i=0;i<8;i=i+1) stripes[i]<=0;
      for (i=0;i<4;i=i+1) level_one[i]<=0;
      for (i=0;i<2;i=i+1) level_two[i]<=0;
      for (i=0;i<5;i=i+1) tag[i]<=0;
    end else if (enable) begin
      tag[0]<=adder_valid ? incoming_tag : 0;
      for (i=1;i<5;i=i+1) tag[i]<=tag[i-1];
      if (retire_valid && !retire_error) begin
        case (tag[4][4:3])
          0: stripes[tag[4][2:0]]<=retire_result;
          1: level_one[tag[4][1:0]]<=retire_result;
          2: level_two[tag[4][0]]<=retire_result;
          default: begin end
        endcase
      end
    end
  end
endmodule
