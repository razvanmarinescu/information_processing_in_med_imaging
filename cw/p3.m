function p3()

bsi = csvread('bsi.csv');

bsi

N = size(bsi,2);

ad1 = bsi(1,1:N/2); % bsi
ctl1 = bsi(1, (N/2)+1:end); % bsi

ad2 = bsi(2,1:N/2); % full volume segmentation difference
ctl2 = bsi(2, (N/2)+1:end); % full volume segmentation difference


[H1_bsi, p1_bsi, CI1_bsi, stats1_bsi] = ttest(ad1, ctl1);
[H2_bsi, p2_bsi, CI2_bsi, stats2_bsi] = ttest2(ad1, ctl1);

[H1_seg, p1_seg, CI1_seg, stats1_seg] = ttest(ad2, ctl2);
[H2_seg, p2_seg, CI2_seg, stats2_seg] = ttest2(ad2, ctl2);

mu_ad_bsi = mean(ad1);
sigma_ad_bsi = std(ad1);
mu_ctl_bsi = mean(ctl1);
sigma_ctl_bsi = std(ctl1);

mu_ad_seg = mean(ad2);
sigma_ad_seg = std(ad2);
mu_ctl_seg = mean(ctl2);
sigma_ctl_seg = std(ctl2);


% bsi - for detecting 25% atrophy reduction between AD and CTL groups with 80% power 
sample_size_bsi = sampsizepwr('t',[mu_ad_bsi sigma_ad_bsi],mu_ad_bsi * 0.75,0.8);

% bsi - for detecting 25% atrophy reduction relative to normal ageing
sample_size_bsi_ageing = sampsizepwr('t',[mu_ctl_bsi sigma_ctl_bsi],mu_ctl_bsi * 0.75,0.8);

% full vol seg - for detecting 25% atrophy reduction between AD and CTL groups with 80% power 
sample_size_seg = sampsizepwr('t',[mu_ad_seg sigma_ad_seg],mu_ad_seg * 0.75,0.8);

% full vol seg - for detecting 25% atrophy reduction relative to normal ageing
sample_size_seg_ageing = sampsizepwr('t',[mu_ctl_seg sigma_ctl_seg],mu_ctl_seg * 0.75,0.8);

plot(ad1)
hold on
plot(ctl1)

end