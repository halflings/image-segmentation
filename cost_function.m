function [costs] = cost_function(img, seeds_obj, seeds_bkg, edges,...
  obj_dist, bkg_dist, K, sigma)

%% img: matrix containing the initial image [MxN]
% obj: pixels of the image that are characterized as object [Nx2]
% bkg: pixels of the image that are characterized as background [Nx2]
% edges: [Lx2] every edge pair contains a number that corresponds to a
%        pixel. the pixels are K = MxN. The obj node is K + 1. The bkg node
%        is K + 2.
% cost: [L] the of every edge if edges correspondingly
lamda = 0;
[rows, columns] = size (img);
pixels = rows * columns;
[num_edges, ~] = size(edges);
costs = zeros(num_edges, 1);
[num_obj, ~] = size(seeds_obj);
[num_bkg, ~] = size(seeds_bkg);


for i = 1:num_edges
  %% Convert edge(i) to rows and columns
  r1 = floor(edges(i, 1) / columns) + 1;
  c1 = i - (r1 - 1) * columns;
  r2 = floor(edges(i, 2) / columns) + 1;
  c2 = i - (r2 - 1) * columns;
  
  if (edges(i, 2) == pixels + 1)
    %% edge to terminal object {p, S}
    % Check if pixel is object or background
    pixel_is = 0;
    for objs = 1:num_obj
      if (r1 == seeds_obj(objs, 1)) && (c1 == seeds_obj(objs, 1))
        pixel_is = 1; % 1 for object
      end
    end
    for bkgs = 1:num_bkg
      if (r1 == seeds_bkg(bkgs, 1)) && (c1 == seeds_bkg(bkgs, 1))
        pixel_is = 2; % 2 for background
      end
    end
    
    if pixel_is == 0
      % Regular pixel, cost = lamda * R("bkg")
      costs(i) = lamda * (-log(normpdf(img(r1, c1), bkg_dist(1), bkg_dist(2))));
      
    elseif pixel_is == 1
      % object pixel
      costs(i) = K;      
    elseif pixel_is == 2
      % background pixel
      costs(i) = 0;
    end
    
  elseif (edges(i, 2) == pixels + 2)
    %% edge to terminal background {p, T}
    % Check if pixel is object or background
    pixel_is = 0;
    for objs = 1:num_obj
      if (r1 == seeds_obj(objs, 1)) && (c1 == seeds_obj(objs, 1))
        pixel_is = 1; % 1 for object
      end
    end
    for bkgs = 1:num_bkg
      if (r1 == seeds_bkg(bkgs, 1)) && (c1 == seeds_bkg(bkgs, 1))
        pixel_is = 2; % 2 for background
      end
    end
    
    if pixel_is == 0
      % Regular pixel, cost = lamda * R("obj")
      costs(i) = lamda * (-log(normpdf(img(r1, c1), obj_dist(1), obj_dist(2))));
      
    elseif pixel_is == 1
      % object pixel
      costs(i) = 0;      
    elseif pixel_is == 2
      % background pixel
      costs(i) = K;
    end
  else
    %% edge of neighboring pixels
    dist = sqrt((r1 - r2) ^ 2 + (c1 - c2) ^ 2);
    %% !!!!!!!!!!! ASSIGN sigma
    B = 1 / dist * exp(- (img(r1, c1) - img(r2, c2)) ^ 2 / (2 * sigma ^ 2));
    costs(i) = B;
  end
end
