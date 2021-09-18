# AUTOGENERATED! DO NOT EDIT! File to edit: nbs/02_sainttabmodel.ipynb (unless otherwise specified).

__all__ = []

# Internal Cell
from fastai.tabular.all import *
import torch.optim as optim

# Internal Cell
#codes from the paper -- https://github.com/somepago/saint/blob/a55fc0ca7ee0a35cf2b88fb692f48a31034b33ef/augmentations.py

def embed_data_mask(x_categ, x_cont, cat_mask, con_mask, model):

    device = x_cont.device
    x_categ = x_categ + model.categories_offset.type_as(x_categ)
    x_categ_enc = model.embeds(x_categ)

    n1,n2 = x_cont.shape
    _, n3 = x_categ.shape

    if model.cont_embeddings == 'MLP':
        x_cont_enc = torch.empty(n1,n2, model.dim)
        for i in range(model.num_continuous):
            x_cont_enc[:,i,:] = model.simple_MLP[i](x_cont[:,i])
    else:
        raise Exception('This case should not work!')


    x_cont_enc = x_cont_enc.to(device)
    cat_mask_temp = cat_mask + model.cat_mask_offset.type_as(cat_mask)
    con_mask_temp = con_mask + model.con_mask_offset.type_as(con_mask)


    cat_mask_temp = model.mask_embeds_cat(cat_mask_temp)
    con_mask_temp = model.mask_embeds_cont(con_mask_temp)
    x_categ_enc[cat_mask == 0] = cat_mask_temp[cat_mask == 0]
    x_cont_enc[con_mask == 0] = con_mask_temp[con_mask == 0]

    return x_categ, x_categ_enc, x_cont_enc


def mixup_data(x1, x2 , lam=1.0, y= None, use_cuda=True):
    '''Returns mixed inputs, pairs of targets'''

    batch_size = x1.size()[0]
    if use_cuda:
        index = torch.randperm(batch_size).cuda()
    else:
        index = torch.randperm(batch_size)


    mixed_x1 = lam * x1 + (1 - lam) * x1[index, :]
    mixed_x2 = lam * x2 + (1 - lam) * x2[index, :]
    if y is not None:
        y_a, y_b = y, y[index]
        return mixed_x1, mixed_x2, y_a, y_b

    return mixed_x1, mixed_x2


def add_noise(x_categ,x_cont, noise_params = {'noise_type' : ['cutmix'],'lambda' : 0.1}):
    lam = noise_params['lambda']
    device = x_categ.device
    batch_size = x_categ.size()[0]

    if 'cutmix' in noise_params['noise_type']:
        index = torch.randperm(batch_size)
        cat_corr = torch.from_numpy(np.random.choice(2,(x_categ.shape),p=[lam,1-lam])).to(device)
        con_corr = torch.from_numpy(np.random.choice(2,(x_cont.shape),p=[lam,1-lam])).to(device)
        x1, x2 =  x_categ[index,:], x_cont[index,:]
        x_categ_corr, x_cont_corr = x_categ.clone().detach() ,x_cont.clone().detach()
        x_categ_corr[cat_corr==0] = x1[cat_corr==0]
        x_cont_corr[con_corr==0] = x2[con_corr==0]
        return x_categ_corr, x_cont_corr
    elif noise_params['noise_type'] == 'gauss':
        print("yet to write this")

#helper functions
def data_prep(data, prob):
    'given a batch of data from fastai dataloader prepares the necessary input'
    if prob == '3pt':
        x_categ = data[0]
        x_cont = data[1]
        y = data[2]
        x_categ = torch.cat([x_categ, y], 1)

        cat_mask = np.ones_like(np.empty((x_categ.shape[0], (x_categ.shape[1]))))
        cat_mask[...,-1] = 0

        con_mask = np.ones_like(np.empty((x_cont.shape[0], (x_cont.shape[1]))))

        cat_mask = tensor(cat_mask).int()
        con_mask = tensor(con_mask).int()

    elif prob == 'fnp':
        x_categ = data[0]
        x_cont = data[1]
        y = data[2]
        x_categ = torch.cat([x_categ, y], 1)
        x_cont.nan_to_num_(0.)

        cat_mask = np.ones_like(np.empty((x_categ.shape[0], (x_categ.shape[1]))))
        cat_mask[...,-1] = 0

        con_mask = torch.where(x_cont==0., 0, 1)

        cat_mask = tensor(cat_mask).int()
        con_mask = tensor(con_mask).int()

    return x_categ, x_cont, cat_mask, con_mask


def data_prep_fnp(data):
    'given a batch of data from fastai dataloader prepares the necessary input'



    return x_categ, x_cont, cat_mask, con_mask


def pt_contrastive(x_categ_enc, x_cont_enc,
                   x_categ_enc_2, x_cont_enc_2,
                   pt_projecthead_style='diff',
                   tmp=0.5):

    'given two sets of categ and cont encodings, builds the contrastive task'

    aug_features_1  = model.transformer(x_categ_enc, x_cont_enc)
    aug_features_2 = model.transformer(x_categ_enc_2, x_cont_enc_2)
    aug_features_1 = (aug_features_1 / aug_features_1.norm(dim=-1, keepdim=True)).flatten(1,2)
    aug_features_2 = (aug_features_2 / aug_features_2.norm(dim=-1, keepdim=True)).flatten(1,2)

    if pt_projecthead_style == 'diff':
        aug_features_1 = model.pt_mlp(aug_features_1)
        aug_features_2 = model.pt_mlp2(aug_features_2)
    elif pt_projecthead_style == 'same':
        aug_features_1 = model.pt_mlp(aug_features_1)
        aug_features_2 = model.pt_mlp(aug_features_2)
    else:
        print('Not using projection head')

    logits_per_aug1 = aug_features_1 @ aug_features_2.t()/config['nce_temp']
    logits_per_aug2 =  aug_features_2 @ aug_features_1.t()/config['nce_temp']
    targets = torch.arange(logits_per_aug1.size(0)).to(logits_per_aug1.device)

    return logits_per_aug1, logits_per_aug2, targets


def get_saint_model(config,
                    cat_dims,
                    num_continuous,
                    continuous_mean_std,
                    y_sim):

    return SAINT(categories = tuple(cat_dims),
                num_continuous = num_continuous,
                dim = config['embedding_size'],
                dim_out = 1,
                depth = config['transformer_depth'],
                heads = config['attention_heads'],
                attn_dropout = config['attention_dropout'],
                ff_dropout = config['ff_dropout'],
                mlp_hidden_mults = (4, 2),
                continuous_mean_std = continuous_mean_std,
                cont_embeddings = config['cont_embeddings'],
                attentiontype = config['attentiontype'],
                final_mlp_style = config['final_mlp_style'],
                y_dim = y_dim)


def get_saint_nsp_dls(fold, train_df, test_df, tp1, tp2, maxtimept, bs):
    features = get_features('data/dataScienceTask/')
    cat_names = ['race', 'gender']
    y_names = 'Stage_Progress'

    df, cont_names = prepare_df_nsetpoints(features, train_df, maxtimept, [tp1, tp2])
    test_df, cont_names = prepare_df_nsetpoints(features, test_df, maxtimept, [tp1, tp2])

    procs = [Categorify, FillMissing(add_col=False), Normalize]

    dls, tabdf = get_tabpandas_dls(fold, df, procs, cat_names, cont_names, y_names, bs)
    test_dl = dls.test_dl(test_df)
    y_dim = 2
    mean, std = list(dls.train.normalize.means.values()), list(dls.train.normalize.stds.values())
    continuous_mean_std = np.array([mean,std]).astype(np.float32)

    categorical_dims = {o:len(i) for o,i in dls.train.categorify.classes.items()}
    cat_dims = list(categorical_dims.values())
    cat_dims.append(2)
    cat_dims = np.array(cat_dims).astype(int)
    num_continuous = len(dls.cont_names)

    return dls, test_dl, tabdf, cat_dims, num_continuous, continuous_mean_std, y_dim


def get_saint_fnp_dls(fold, train_df, test_df, n_tp, maxtimept, bs):
    features = get_features('data/dataScienceTask/')
    cat_names = ['race', 'gender']
    y_names = 'Stage_Progress'

    df, cont_names = prepare_df_firstnpoints(features, train_df, n_tp, maxtimept)
    test_df, cont_names = prepare_df_firstnpoints(features, test_df, n_tp, maxtimept)
    constants = {k:1000. for k in cont_names}
    procs = [Categorify, Normalize]

    dls, tabdf = get_tabpandas_dls(fold, df, procs, cat_names, cont_names, y_names, bs)
    test_dl = dls.test_dl(test_df)
    y_dim = 2
    mean, std = list(dls.train.normalize.means.values()), list(dls.train.normalize.stds.values())
    continuous_mean_std = np.array([mean,std]).astype(np.float32)

    categorical_dims = {o:len(i) for o,i in dls.train.categorify.classes.items()}
    cat_dims = list(categorical_dims.values())
    cat_dims.append(2)
    cat_dims = np.array(cat_dims).astype(int)
    num_continuous = len(dls.cont_names)

    return dls, test_dl, tabdf, cat_dims, num_continuous, continuous_mean_std, y_dim


def pt_train_loop(dls, model, config):

    pt_aug_dict = {'noise_type' : config['pt_aug'],
                  'lambda' : config['pt_aug_lam'] }

    criterion = nn.CrossEntropyLoss().to(device)
    criterion1 = nn.CrossEntropyLoss()
    criterion2 = nn.MSELoss()
    optimizer = optim.AdamW(model.parameters(),lr=config['lr'])

    for epoch in range(config['pretrain_epochs']):

        model.train()
        running_loss = 0.0
        for i, data in enumerate(dls.train):

            x_categ, x_cont, cat_mask, con_mask = data_prep(data)

            #input without augs
            _ , x_categ_enc, x_cont_enc = embed_data_mask(x_categ, x_cont, cat_mask, con_mask, model)

            # embed_data_mask function is used to embed both categorical and continuous data.
            # cutmix
            x_categ_corr, x_cont_corr = add_noise(x_categ, x_cont, noise_params = pt_aug_dict)
            _ , x_categ_enc_2, x_cont_enc_2 = embed_data_mask(x_categ_corr, x_cont_corr, cat_mask, con_mask, model)

            #mixup
            x_categ_enc_2, x_cont_enc_2 = mixup_data(x_categ_enc_2, x_cont_enc_2 , lam=config['mixup_lam'], use_cuda=False)

            loss = 0
            if 'contrastive' in config['pt_tasks']:
                logits_per_aug1, logits_per_aug2, targets = pt_contrastive(x_categ_enc, x_cont_enc,
                                                                          x_categ_enc_2, x_cont_enc_2,
                                                                          config['pt_projhead_style'],
                                                                          config['nce_temp'])
                loss_1 = criterion(logits_per_aug1, targets)
                loss_2 = criterion(logits_per_aug2, targets)
                loss   = config['lam0']*(loss_1 + loss_2)/2

            if 'denoising' in config['pt_tasks']:
                cat_outs, con_outs = model(x_categ_enc_2, x_cont_enc_2)
                con_outs =  torch.cat(con_outs,dim=1)
                l2 = criterion2(con_outs, x_cont)
                l1 = 0
                for j in range(len(cat_dims)-1):
                    l1+= criterion1(cat_outs[j], x_categ[:,j])

            loss += config['lam2']*l1 + config['lam3']*l2
            loss.backward()
            optimizer.step()
            running_loss += loss.item()

        print(f'Epoch: {epoch}, Running Loss: {running_loss/len(dls.train):.4f}')


def training(dls, model, config, output_fn, prob):
    optimizer = optim.AdamW(model.parameters(),lr=config['lr'])

    #weight=tensor([0.67, 1.33])
    criterion = nn.CrossEntropyLoss().to(device)
    scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=1e-1)
    best_acc = 0
    for epoch in range(config['epochs']):

        #train loop
        model.train()
        running_tloss = 0.0
        for data in dls.train:
            optimizer.zero_grad()

            # x_categ is the the categorical data, with y appended as last feature.
            #x_cont has continuous data.
            #cat_mask is an array of ones same shape as x_categ except for last column(corresponding to y's) set to 0s.
            #con_mask is an array of ones same shape as x_cont.
            x_categ, x_cont, cat_mask, con_mask = data_prep(data, prob)

            # We are converting the data to embeddings in the next step
            _ , x_categ_enc, x_cont_enc = embed_data_mask(x_categ, x_cont, cat_mask, con_mask, model)
            reps = model.transformer(x_categ_enc, x_cont_enc)

            # select only the representations corresponding to y and apply mlp on it in the next step to get the predictions.
            y_reps = reps[:,len(cat_dims)-1,:]
            y_outs = model.mlpfory(y_reps)
            loss = criterion(y_outs, x_categ[:,len(cat_dims)-1])
            loss.backward()
            optimizer.step()
            running_tloss += loss.item()

        #valid loop
        model.eval()
        running_vloss = 0.0
        m = nn.Softmax(dim=1)
        y_test = torch.empty(0).to(device)
        y_pred = torch.empty(0).to(device)

        with torch.no_grad():
            for data in dls.valid:
                x_categ, x_cont, cat_mask, con_mask = data_prep(data, prob)
                _ , x_categ_enc, x_cont_enc = embed_data_mask(x_categ, x_cont, cat_mask, con_mask, model)

                reps = model.transformer(x_categ_enc, x_cont_enc)
                y_reps = reps[:,model.num_categories-1,:]

                y_outs = model.mlpfory(y_reps)
                v_loss = criterion(y_outs, x_categ[:,len(cat_dims)-1])

                y_test = torch.cat([y_test, x_categ[:,-1].float()],dim=0)
                y_pred = torch.cat([y_pred, torch.argmax(m(y_outs), dim=1).float()],dim=0)
                running_vloss += v_loss.item()

        correct_results_sum = (y_pred == y_test).sum().float()
        acc = correct_results_sum/y_test.shape[0]*100

        if acc > best_acc:
            print(f'Found new best model with accuracy of {acc} : Epoch {epoch}')
            best_acc = acc
            torch.save(model.state_dict(), output_fn)
        print(f'Epoch: {epoch}, Train Loss: {running_tloss/len(dls.train):.4f}, Valid Loss: {running_vloss/len(dls.valid):.4f}, Valid Acc: {acc:.2f}')
        model.train()


def test(test_dl, prob):
    model.eval()
    y_test = torch.empty(0).to(device)
    y_pred = torch.empty(0).to(device)

    with torch.no_grad():
        for data in test_dl:
            x_categ, x_cont, cat_mask, con_mask = data_prep(data, prob)
            _ , x_categ_enc, x_cont_enc = embed_data_mask(x_categ, x_cont, cat_mask, con_mask, model)

            reps = model.transformer(x_categ_enc, x_cont_enc)
            y_reps = reps[:,model.num_categories-1,:]

            y_outs = model.mlpfory(y_reps)

            y_test = torch.cat([y_test, x_categ[:,-1].float()],dim=0)
            y_pred = torch.cat([y_pred, y_outs],dim=0)

    return y_test, y_pred