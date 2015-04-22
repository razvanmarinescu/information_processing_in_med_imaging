function p1_plots()

dice = zeros(4,4,10);
dice(1,:,:) = csvread('dice_l0.txt');
dice(2,:,:) = csvread('dice_l1.txt');
dice(3,:,:) = csvread('dice_l2.txt');
dice(4,:,:) = csvread('dice_l3.txt');

dice_mean = mean(dice,3);
dice_std = std(dice,0,3);

h = figure
for iter=1:4
  %plot(dice_mean(iter,:), 'linewidth',2);
  plot(2:5,dice_mean(:,iter), 'linewidth',2);
  %barwitherr(dice_std(:,iter), 2:5,dice_mean(:,iter))
  hold on 
end

xlabel('number of levels')
ylabel('dice score')
legend('50 iterations','150 iterations','200 iterations','300 iterations','location', 'northoutside')
set(gca,'FontSize',12);
ax = gca
ax.XTick = 2:5

hgexport(h, 'report/figures/dice_params.eps');


end