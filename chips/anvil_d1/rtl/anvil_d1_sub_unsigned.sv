module anvil_d1_sub_unsigned #(
  parameter integer WIDTH=128,
  localparam integer W=(WIDTH>=1 && WIDTH<=129) ? WIDTH : 1,
  localparam integer N=(W+15)/16,
  localparam integer LEVELS=$clog2(N)
) (
  input wire [W-1:0] a, b,
  output wire [W-1:0] difference,
  output wire borrow
);
  wire [N*16-1:0] pa={{(N*16-W){1'b0}},a};
  wire [N*16-1:0] pb={{(N*16-W){1'b0}},b};
  wire [N-1:0] g [0:LEVELS];
  wire [N-1:0] p [0:LEVELS];
  wire [N:0] carry;
  wire [N*16-1:0] result;
  assign carry[0]=1'b1;
  assign difference=result[W-1:0];
  assign borrow=!carry[N];
  genvar i, l;
  generate
    if (WIDTH<1 || WIDTH>129) begin: invalid_parameters
      initial $fatal(1,"ANVIL_D1 PARAMETER ERROR: subtract width");
    end
    for (i=0;i<N;i=i+1) begin: chunks
      wire [16:0] base={1'b0,pa[i*16+:16]}+{1'b0,~pb[i*16+:16]};
      assign g[0][i]=base[16];
      assign p[0][i]=&base[15:0];
      assign carry[i+1]=g[LEVELS][i] | p[LEVELS][i];
      assign result[i*16+:16]=base[15:0]+{{15{1'b0}},carry[i]};
    end
    for (l=0;l<LEVELS;l=l+1) begin: levels
      for (i=0;i<N;i=i+1) begin: prefixes
        if (i>=(1<<l)) begin: combine
          assign g[l+1][i]=g[l][i] | (p[l][i] & g[l][i-(1<<l)]);
          assign p[l+1][i]=p[l][i] & p[l][i-(1<<l)];
        end else begin: pass
          assign g[l+1][i]=g[l][i];
          assign p[l+1][i]=p[l][i];
        end
      end
    end
  endgenerate
endmodule
