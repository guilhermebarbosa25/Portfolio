import sys
import numpy as np
import pandas as pd
import math
import time
import warnings

start_time = time.time()

fname = str(sys.argv[1])
fname2 = str(sys.argv[2])

warnings.filterwarnings("ignore")


print("LEITURA...%.2f seconds up to now"%(time.time() - start_time))
#                    LEITURA DOS ARQUIVOS
#_______________________________________________________________________
ratings = np.loadtxt(open(fname, "rb"), delimiter=",", skiprows=0, dtype= str)
targets = np.loadtxt(open(fname2, "rb"), delimiter=",", skiprows=0, dtype= str)




print("ARMAZENAMENTO E TRATAMENTO...%.2f seconds up to now"%(time.time() - start_time))
#    ARMAZENAMENTO DAS RATINGS COMO LISTA, RETIRADA DE CABECALHO E DE LETRAS
#_______________________________________________________________________
usersitens = np.loadtxt(ratings[:,0], delimiter=":", skiprows=0, dtype= str)
usersitens[1:,0] = [x[1:] for x in usersitens[1:,0]]
usersitens[1:,1] = [x[1:] for x in usersitens[1:,1]]





print("CRIACAO DO DATAFRAME...%.2f seconds up to now"%(time.time() - start_time))
#                       CRIACAO DO DATAFRAME
#_______________________________________________________________________
RatingDf = pd.DataFrame({'users': usersitens[1:,0],'movies': usersitens[1:,1], 'grades': ratings[1:,1]})
RatingDf['grades'] = RatingDf['grades'].astype('int16')
RatingDf['users'] = RatingDf['users'].astype('int32')
RatingDf['movies'] = RatingDf['movies'].astype('int32')
#_______________________________________________________________________





print("PIVOT DOS RATINGS PARA UMA MATRIZ...%.2f seconds up to now"%(time.time() - start_time))
#                    PIVOT DOS RATINGS PARA UMA MATRIZ
#_______________________________________________________________________
RatingMatrix = RatingDf.pivot(index='users', columns='movies', values='grades')
del(RatingDf)
del(usersitens)
del(ratings)
#_______________________________________________________________________





print("NORMALIZACAO DOS RATINGS...%.2f seconds up to now"%(time.time() - start_time))
#                      NORMALIZACAO DOS RATINGS
#_______________________________________________________________________
#for idx in RatingMatrix.index:
#      RatingMatrix.loc[idx,:] -=  np.mean(RatingMatrix.loc[idx,:],axis=1,keepdims=True)
#_______________________________________________________________________





print("TRANSFORMACAO DO DATAFRAME EM ARRAY...%.2f seconds up to now"%(time.time() - start_time))
#      TRANSFORMACAO DO DATAFRAME EM ARRAY NUMPY(ECONOMIZAR MEMORIA)
#_______________________________________________________________________
numrows = RatingMatrix.shape[0]
index = RatingMatrix.index
movies = RatingMatrix.columns
NormRating = RatingMatrix.values.astype('float32')
NormRating[np.isnan(NormRating)] = 0.0
del(RatingMatrix)
#_______________________________________________________________________


print("CALCULO DAS SIMILARIDADES...%.2f seconds up to now"%(time.time() - start_time))
#                    CALCULO DAS SIMILARIDADES
#_______________________________________________________________________
SimMatrix = np.zeros((1 ,1), dtype='float32')
C = np.zeros((1 ,1), dtype='float32')
D = np.zeros((1 ,1), dtype='float32')


C = (NormRating.T * NormRating.T).sum(0, keepdims=True) ** .5
D = NormRating / C.T
D=np.nan_to_num(D,copy=False,nan=0.0, posinf=0.0, neginf=0.0)
del(C)
SimMatrix = D @ D.T
del(D)
SimMatrix=np.nan_to_num(SimMatrix,copy=False,nan=0.0, posinf=0.0, neginf=0.0)






print("LEITURA TARGETS...%.2f seconds up to now"%(time.time() - start_time))
#                   PREPARACAO DOS TARGETS
#_______________________________________________________________________
usersitens = np.loadtxt(targets[:], delimiter=":", skiprows=0, dtype= str)
usersitens[:,0] = [x[1:] for x in usersitens[:,0]]
usersitens[:,1] = [x[1:] for x in usersitens[:,1]]
users_rec = np.asarray(usersitens[1:,0]).astype('int64')
movs_rec = np.asarray(usersitens[1:,1]).astype('int64')
del(usersitens)
#_______________________________________________________________________






print("PROCESSAMENTO DAS RECOMENDACOES...%.2f seconds up to now"%(time.time() - start_time))
#                  PROCESSAMENTO DAS RECOMENDACOES
#____________________________________________________________
cold_user=False
cold_mov=False
media_global = np.mean(NormRating[np.nonzero(NormRating[:,:])])
recomendation = np.zeros(np.loadtxt(targets[1:], skiprows=0, dtype= str).shape[0], dtype=[('targets', 'U32'), ('recs', float)])
recomendation['targets'] = np.loadtxt(targets[1:], skiprows=0, dtype= str)
for r in range(0,users_rec.shape[0]):
      user = users_rec[r]
      mov = movs_rec[r] 

      if(len(np.where(index==user)[0]) == 0):
          cold_user = True
      else:
          cold_user = False
      if(len(np.where(movies==mov)[0]) == 0):
          cold_mov  = True
      else:
          cold_mov = False

      if(cold_user==False and cold_mov  == False):
          ind_user = np.where(index==user)[0][0]
          ind_mov = np.where(movies==mov)[0][0]
          ind_UsersRtdMov = np.asarray(np.where(NormRating[:,ind_mov]>0)[0])
          ind_similars = np.asarray(np.where(SimMatrix[ind_user,:]!=0)[0])
          ind_rated_sim = np.where(np.in1d(ind_similars,ind_UsersRtdMov)==True)[0]
          ind_rated_sim = ind_similars[ind_rated_sim]
          sim_rated = SimMatrix[ind_user, ind_rated_sim]
          topk_ind = ind_rated_sim[sim_rated.argsort()[-30:][::-1]]
          topk_sim = SimMatrix[ind_user,topk_ind]
          topk_rates = NormRating[topk_ind,ind_mov]
          if(topk_sim.shape[0]==0):
               recomendation_now = np.mean(NormRating[ind_UsersRtdMov,ind_mov])
               #recomendation_now = np.mean(NormRating[ind_user,np.nonzero(NormRating[ind_user,:])])
          else:
               recomendation_now = sum(np.multiply(topk_sim,topk_rates))/sum(topk_sim)
                               
      elif(cold_user==False and cold_mov  == True):
          ind_user = np.where(index==user)[0][0]
          recomendation_now = np.mean(NormRating[ind_user,np.nonzero(NormRating[ind_user,:])])

      elif(cold_user==True and cold_mov==False):
          ind_mov = np.where(movies==mov)[0][0]
          ind_UsersRtdMov = np.asarray(np.where(NormRating[:,ind_mov]>0)[0])
          recomendation_now = np.mean(NormRating[ind_UsersRtdMov,ind_mov])
          
      elif(cold_user==True and cold_mov==True):
          recomendation_now = media_global
          
      recomendation['recs'][r] = recomendation_now

#____________________________________________________________
np.savetxt("saida.csv", recomendation, fmt='%s,%.4f', delimiter=',\n', header='UserId:ItemId,Prediction',comments='')
print("Tempo Final: %.2f seconds" % (time.time() - start_time))
