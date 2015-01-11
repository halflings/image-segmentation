function [costs, edges] = calc_costs(image, seeds_obj, seeds_bkg)

sigma = 0;

[rows, columns] = size(image);
pixels = rows * columns;

%% Create edges
edge = 1;
for i = 1:rows
  for j = 1:columns
    pix = (i - 1) * columns + j;
    %% Add edges to terminals
    edges(edge, 1) = pix;
    edges(edge, 2) = pixels + 1; % Edge to obj terminal
    edge = edge + 1;
    edges(edge, 1) = pix;
    edges(edge, 2) = pixels + 2; % Edge to bkg terminal
    edge = edge + 1;
    
    %% Add neighboring edges
    if (j == columns) && (i ~= rows)
      %% right side of the image
      edges(edge, 1) = pix;
      edges(edge, 2) = pix + columns;
      edge = edge + 1;
    elseif (j ~= columns) && (i == rows)
      %% down side of the image
      edges(edge, 1) = pix;
      edges(edge, 2) = pix + 1;
      edge = edge + 1;
    elseif (j ~= columns) && (i ~= rows)
      edges(edge, 1) = pix;
      edges(edge, 2) = pix + 1;
      edge = edge + 1;
      edges(edge, 1) = pix;
      edges(edge, 2) = pix + columns;
      edge = edge + 1;
      edges(edge, 1) = pix;
      edges(edge, 2) = pix + columns + 1;
      edge = edge + 1;
    end
  end
end
edge = edge - 1;
%% Calculate K
max_p = 0;
for pix = 1:pixels
  s = 0;
  for e = 1:edge
    if (edges(e, 1) == pix && edges(e, 2) == pixels + 1 &&...
        edges(e, 2) == pixels + 2) || (edges(e, 2) == pix)
      %% Convert edge(i) to rows and columns
      r1 = floor(edges(i, 1) / columns) + 1;
      c1 = i - (r1 - 1) * columns;
      r2 = floor(edges(i, 2) / columns) + 1;
      c2 = i - (r2 - 1) * columns;
      
      dist = sqrt((r1 - r2) ^ 2 + (c1 - c2) ^ 2);
      %% !!!!!!!!!!! ASSIGN sigma
      B = 1 / dist * exp(- (image(r1, c1) - image(r2, c2)) ^ 2 /...
        (2 * sigma ^ 2));
      s = s + B;
    end
  end
  if s > max
    max = s;
  end
end
K + 1 + max;

%% Calculate prob distributions
obj_dist(1) = mean(seeds_obj);
obj_dist(2) = std(seeds_obj);
bkg_dist(1) = mean(seeds_bkg);
bkg_dist(2) = std(seeds_bkg);

costs = cost_function(image, seeds_obj, seeds_bkg, edges, obj_dist,...
  bkg_dist, K, sigma);
